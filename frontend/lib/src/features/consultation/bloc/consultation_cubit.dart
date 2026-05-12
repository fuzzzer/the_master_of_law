import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

part 'consultation_state.dart';

class RagConfigPresets {
  RagConfigPresets._();
  static const lawsOnly = <String, dynamic>{
    'legal_codes': true, 'court_practice': false, 'grand_chamber': false,
  };
  static const allSources = <String, dynamic>{
    'legal_codes': true, 'court_practice': true, 'grand_chamber': true,
  };
}

enum ChatMode {
  lawsOnly,
  allSources;

  Map<String, dynamic> get ragConfig => switch (this) {
    ChatMode.lawsOnly => RagConfigPresets.lawsOnly,
    ChatMode.allSources => RagConfigPresets.allSources,
  };

  String get labelKa => switch (this) {
    ChatMode.lawsOnly => 'კანონები',
    ChatMode.allSources => 'ყველა წყარო',
  };
}

class ConsultationCubit extends Cubit<ConsultationState> {
  final ConsultationRepository _repository;

  ConsultationCubit({
    required ConsultationRepository repository,
    ChatMode chatMode = ChatMode.allSources,
    bool isCaseChat = false,
  })  : _repository = repository,
        super(ConsultationState(chatMode: chatMode, isCaseChat: isCaseChat));

  Future<void> startConversation({String? caseId}) async {
    emit(state.copyWith(status: StateStatus.loading));
    final result = await _repository.createConversation(caseId: caseId);
    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        emit(state.copyWith(
          status: StateStatus.success,
          conversationId: data['id'] as String? ?? '',
          messages: [],
        ));
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        emit(state.copyWith(status: StateStatus.failed, failureType: type));
    }
  }

  Future<void> loadConversation(String conversationId) async {
    emit(state.copyWith(status: StateStatus.loading, conversationId: conversationId));
    final result = await _repository.getConversation(conversationId);
    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        final rawMessages = data['messages'] as List<dynamic>? ?? [];
        final messages = rawMessages.map((m) {
          final map = m as Map<String, dynamic>;
          return ChatMessage(
            id: map['id']?.toString() ?? '',
            text: map['content']?.toString() ?? '',
            isUser: map['role'] == 'user',
            timestamp: DateTime.tryParse(map['created_at']?.toString() ?? '') ?? DateTime.now(),
            citations: _parseCitations(map['citations']),
            trustLevel: map['trust_level']?.toString(),
          );
        }).toList();
        final caseReady = data['case_ready'] == true;
        emit(state.copyWith(status: StateStatus.success, messages: messages, caseAnalysisReady: caseReady));
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        emit(state.copyWith(status: StateStatus.failed, failureType: type));
    }
  }

  Future<void> sendMessage(String text) async {
    if (state.conversationId == null) return;
    final userMsg = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      text: text, isUser: true, timestamp: DateTime.now(),
    );
    
    final streamingId = 'stream_${DateTime.now().millisecondsSinceEpoch}';
    final aiMsg = ChatMessage(
      id: streamingId,
      text: '', isUser: false, timestamp: DateTime.now(),
    );

    emit(state.copyWith(
      messages: [...state.messages, userMsg, aiMsg], 
      isSending: true,
      streamingMessageId: streamingId,
      clearStreamingStatus: true,
    ));

    final stream = _repository.streamMessage(
      conversationId: state.conversationId!,
      message: text,
      ragConfig: state.chatMode.ragConfig,
      mode: state.isCaseChat ? 'case_intake' : 'chat',
      caseContext: state.attachedCaseContext,
      caseFileId: state.caseFileId,
    );

    final toolResultsCollected = <ToolResultData>[];

    try {
      await for (final event in stream) {
        final type = event['type'];
        if (type == 'status') {
          emit(state.copyWith(streamingStatus: event['message']?.toString()));
        } else if (type == 'chunk') {
          final msgs = List<ChatMessage>.from(state.messages);
          final index = msgs.indexWhere((m) => m.id == streamingId);
          if (index != -1) {
            final oldMsg = msgs[index];
            msgs[index] = ChatMessage(
              id: oldMsg.id,
              text: oldMsg.text + (event['content']?.toString() ?? ''),
              isUser: false,
              timestamp: oldMsg.timestamp,
            );
            emit(state.copyWith(messages: msgs, clearStreamingStatus: true));
          }
        } else if (type == 'tool_executed') {
          toolResultsCollected.add(ToolResultData(
            toolName: event['tool']?.toString() ?? '',
            status: event['status']?.toString() ?? 'executed',
            result: (event['result'] as Map<String, dynamic>?) ?? {},
          ));
          emit(state.copyWith(
            streamingStatus: '🔧 ${_toolNameKa(event['tool']?.toString() ?? '')}',
          ));
        } else if (type == 'confirmation_required') {
          final pending = ToolResultData(
            toolName: event['tool_name']?.toString() ?? '',
            status: 'pending_confirmation',
            requiresConfirmation: true,
            confirmationId: event['confirmation_id']?.toString(),
            description: event['description']?.toString(),
          );
          toolResultsCollected.add(pending);
          emit(state.copyWith(
            pendingConfirmations: [...state.pendingConfirmations, pending],
          ));
        } else if (type == 'done') {
          final msgs = List<ChatMessage>.from(state.messages);
          final index = msgs.indexWhere((m) => m.id == streamingId);
          if (index != -1) {
            final oldMsg = msgs[index];
            msgs[index] = ChatMessage(
              id: oldMsg.id,
              text: event['full_response']?.toString() ?? oldMsg.text,
              isUser: false,
              timestamp: oldMsg.timestamp,
              citations: _parseChatCitations(event['citations']),
              trustLevel: event['trust_level']?.toString(),
              toolResults: toolResultsCollected.isNotEmpty ? toolResultsCollected : null,
            );
            emit(state.copyWith(
              messages: msgs,
              isSending: false,
              clearStreamingStatus: true,
              clearStreamingMessageId: true,
              caseAnalysisReady: event['case_analysis_ready'] == true,
            ));
          }
          break;
        } else if (type == 'error') {
          final errorMsg = ChatMessage(
            id: 'error_${DateTime.now().millisecondsSinceEpoch}',
            text: event['message']?.toString() ?? 'An error occurred',
            isUser: false, timestamp: DateTime.now(),
            isError: true, failureType: ConsultationFailureType.unknown,
          );
          
          final msgs = List<ChatMessage>.from(state.messages);
          msgs.removeWhere((m) => m.id == streamingId);
          
          emit(state.copyWith(
            messages: [...msgs, errorMsg], 
            isSending: false,
            clearStreamingStatus: true,
            clearStreamingMessageId: true,
          ));
          break;
        }
      }
    } catch (e) {
      final errorMsg = ChatMessage(
        id: 'error_${DateTime.now().millisecondsSinceEpoch}',
        text: 'Connection error',
        isUser: false, timestamp: DateTime.now(),
        isError: true, failureType: ConsultationFailureType.network,
      );
      
      final msgs = List<ChatMessage>.from(state.messages);
      msgs.removeWhere((m) => m.id == streamingId);
      
      emit(state.copyWith(
        messages: [...msgs, errorMsg], 
        isSending: false,
        clearStreamingStatus: true,
        clearStreamingMessageId: true,
      ));
    }
  }

  String _toolNameKa(String name) => switch (name) {
    'add_fact' => 'ფაქტი დამატებულია',
    'edit_fact' => 'ფაქტი განახლდა',
    'add_argument' => 'არგუმენტი დამატებულია',
    'link_article' => 'მუხლი მიბმულია',
    'set_strategy' => 'სტრატეგია დაყენებულია',
    'add_action_item' => 'დავალება დამატებულია',
    'add_risk' => 'რისკი დამატებულია',
    'get_case_summary' => 'საქმის მიმოხილვა',
    _ => name,
  };

  Future<Map<String, dynamic>?> buildCaseFile() async {
    if (state.conversationId == null) return null;
    emit(state.copyWith(isBuildingCase: true));

    final result = await _repository.buildCaseFile(
      conversationId: state.conversationId!,
    );
    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        emit(state.copyWith(isBuildingCase: false, caseFileData: data));
        return data;
      case ConsultationFailure<Map<String, dynamic>>():
        emit(state.copyWith(isBuildingCase: false));
        return null;
    }
  }

  void switchMode(ChatMode mode) => emit(state.copyWith(chatMode: mode));

  void attachCase({required String caseId, required String caseTitle, required String caseContext}) {
    emit(state.copyWith(
      attachedCaseId: caseId,
      attachedCaseTitle: caseTitle,
      attachedCaseContext: caseContext,
    ));
  }

  void detachCase() {
    emit(state.copyWith(
      clearAttachedCase: true,
    ));
  }

  void injectMessage(ChatMessage message) {
    emit(state.copyWith(
      messages: [...state.messages, message],
    ));
  }

  void enterAgentMode({required String caseFileId}) {
    emit(state.copyWith(caseFileId: caseFileId));
  }

  void exitAgentMode() {
    emit(state.copyWith(clearCaseFileId: true, pendingConfirmations: []));
  }

  Future<void> sendAgentMessage(String text) async {
    if (state.conversationId == null || state.caseFileId == null) return;
    final userMsg = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      text: text, isUser: true, timestamp: DateTime.now(),
    );
    emit(state.copyWith(messages: [...state.messages, userMsg], isSending: true));

    final result = await _repository.sendAgentMessage(
      conversationId: state.conversationId!,
      message: text,
      caseFileId: state.caseFileId!,
      ragConfig: state.chatMode.ragConfig,
    );
    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        final toolResults = _parseToolResults(data['tool_results']) ?? [];
        final pendingOnes = toolResults
            .where((t) => t.requiresConfirmation)
            .toList();
        final aiMsg = ChatMessage(
          id: data['id']?.toString() ?? DateTime.now().millisecondsSinceEpoch.toString(),
          text: data['response']?.toString() ?? '',
          isUser: false,
          timestamp: DateTime.now(),
          citations: _parseChatCitations(data['citations']),
          toolResults: toolResults,
        );
        emit(state.copyWith(
          messages: [...state.messages, aiMsg],
          isSending: false,
          pendingConfirmations: [...state.pendingConfirmations, ...pendingOnes],
        ));
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        final errorMsg = ChatMessage(
          id: 'error_${DateTime.now().millisecondsSinceEpoch}',
          text: type.name, isUser: false, timestamp: DateTime.now(),
          isError: true, failureType: type,
        );
        emit(state.copyWith(messages: [...state.messages, errorMsg], isSending: false));
    }
  }

  Future<void> confirmToolAction(String confirmationId) async {
    if (state.conversationId == null) return;
    final result = await _repository.confirmToolAction(
      conversationId: state.conversationId!,
      confirmationId: confirmationId,
      confirmed: true,
    );
    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        final updatedPending = state.pendingConfirmations
            .where((t) => t.confirmationId != confirmationId)
            .toList();
        final confirmMsg = ChatMessage(
          id: 'conf_${DateTime.now().millisecondsSinceEpoch}',
          text: '✅ ${data['tool_name']}: შესრულდა',
          isUser: false,
          timestamp: DateTime.now(),
        );
        emit(state.copyWith(
          messages: [...state.messages, confirmMsg],
          pendingConfirmations: updatedPending,
        ));
      case ConsultationFailure<Map<String, dynamic>>():
        break;
    }
  }

  Future<void> rejectToolAction(String confirmationId) async {
    if (state.conversationId == null) return;
    final result = await _repository.confirmToolAction(
      conversationId: state.conversationId!,
      confirmationId: confirmationId,
      confirmed: false,
    );
    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        final updatedPending = state.pendingConfirmations
            .where((t) => t.confirmationId != confirmationId)
            .toList();
        final rejectMsg = ChatMessage(
          id: 'reject_${DateTime.now().millisecondsSinceEpoch}',
          text: '❌ ${data['tool_name']}: გაუქმებულია',
          isUser: false,
          timestamp: DateTime.now(),
        );
        emit(state.copyWith(
          messages: [...state.messages, rejectMsg],
          pendingConfirmations: updatedPending,
        ));
      case ConsultationFailure<Map<String, dynamic>>():
        break;
    }
  }

  List<ToolResultData>? _parseToolResults(dynamic raw) {
    if (raw is! List) return null;
    return raw.map((t) {
      final map = t as Map<String, dynamic>;
      return ToolResultData(
        toolName: map['tool_name']?.toString() ?? '',
        status: map['status']?.toString() ?? '',
        result: (map['result'] as Map<String, dynamic>?) ?? {},
        requiresConfirmation: map['requires_confirmation'] == true,
        confirmationId: map['confirmation_id']?.toString(),
        description: map['description']?.toString(),
      );
    }).toList();
  }

  List<CitationData>? _parseCitations(dynamic raw) {
    if (raw is! List) return null;
    return raw.map((c) {
      final map = c as Map<String, dynamic>;
      return CitationData(
        articleId: map['article_id']?.toString() ?? '',
        articleTitle: map['article_title']?.toString() ?? '',
        codeTitle: map['code_title']?.toString() ?? '',
        snippet: map['snippet']?.toString() ?? '',
        trustLevel: map['trust_level']?.toString() ?? 'guidance',
      );
    }).toList();
  }

  List<CitationData>? _parseChatCitations(dynamic raw) {
    if (raw is! List) return null;
    return raw.map((c) {
      final map = c as Map<String, dynamic>;
      return CitationData(
        articleId: map['article_number']?.toString() ?? map['article_id']?.toString() ?? '',
        articleTitle: map['raw_text']?.toString() ?? map['article_title']?.toString() ?? '',
        codeTitle: map['code_name']?.toString() ?? map['code_title']?.toString() ?? '',
        snippet: map['citation_text']?.toString() ?? map['snippet']?.toString() ?? '',
        trustLevel: map['verified'] == true ? 'verified' : 'guidance',
      );
    }).toList();
  }

  void reset() {
    emit(ConsultationState(chatMode: state.chatMode, isCaseChat: state.isCaseChat));
  }
}

