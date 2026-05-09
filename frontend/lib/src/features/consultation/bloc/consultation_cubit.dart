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
    emit(state.copyWith(messages: [...state.messages, userMsg], isSending: true));

    final result = await _repository.sendMessage(
      conversationId: state.conversationId!,
      message: text,
      ragConfig: state.chatMode.ragConfig,
      mode: state.isCaseChat ? 'case_intake' : 'chat',
      caseContext: state.attachedCaseContext,
    );
    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        final aiMsg = ChatMessage(
          id: data['id']?.toString() ?? DateTime.now().millisecondsSinceEpoch.toString(),
          text: data['response']?.toString() ?? data['content']?.toString() ?? '',
          isUser: false,
          timestamp: DateTime.tryParse(data['created_at']?.toString() ?? '') ?? DateTime.now(),
          citations: _parseChatCitations(data['citations']),
          trustLevel: data['trust_level']?.toString(),
        );
        final caseAnalysisReady = data['case_analysis_ready'] == true;
        final updatedMessages = [...state.messages, aiMsg];
        emit(state.copyWith(
          messages: updatedMessages,
          isSending: false,
          caseAnalysisReady: caseAnalysisReady,
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

