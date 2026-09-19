import 'dart:async';

import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';

part 'consultation_state.dart';

class RagConfigPresets {
  RagConfigPresets._();
  static const lawsOnly = <String, dynamic>{
    'legal_codes': true,
    'court_practice': false,
    'grand_chamber': false,
  };
  static const allSources = <String, dynamic>{
    'legal_codes': true,
    'court_practice': true,
    'grand_chamber': true,
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

  /// Active WebSocket stream subscription for the in-flight message, if any.
  /// Cancelled in [close] so the cubit never emits after disposal (F-02/F-03).
  StreamSubscription<Map<String, dynamic>>? _streamSubscription;

  ConsultationCubit({
    required ConsultationRepository repository,
    ChatMode chatMode = ChatMode.allSources,
    bool isCaseChat = false,
  }) : _repository = repository,
       super(ConsultationState(chatMode: chatMode, isCaseChat: isCaseChat));

  /// Emit only while the cubit is still open. Streaming responses are
  /// long-lived; the user can navigate away mid-stream, so every emit on an
  /// async path must be guarded against the closed state.
  void _safeEmit(ConsultationState newState) {
    if (isClosed) return;
    emit(newState);
  }

  @override
  Future<void> close() {
    _streamSubscription?.cancel();
    _streamSubscription = null;
    return super.close();
  }

  Future<void> startConversation({String? caseId}) async {
    _safeEmit(state.copyWith(status: StateStatus.loading));
    final result = await _repository.createConversation(caseId: caseId);
    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        _safeEmit(
          state.copyWith(
            status: StateStatus.success,
            conversationId: data['id'] as String? ?? '',
            messages: [],
          ),
        );
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        _safeEmit(
          state.copyWith(status: StateStatus.failed, failureType: type),
        );
    }
  }

  Future<void> loadConversation(String conversationId) async {
    _safeEmit(
      state.copyWith(
        status: StateStatus.loading,
        conversationId: conversationId,
      ),
    );
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
            timestamp:
                DateTime.tryParse(map['created_at']?.toString() ?? '') ??
                DateTime.now(),
            citations: _parseCitations(map['citations']),
            trustLevel: map['trust_level']?.toString(),
          );
        }).toList();
        final caseReady = data['case_ready'] == true;
        _safeEmit(
          state.copyWith(
            status: StateStatus.success,
            messages: messages,
            caseAnalysisReady: caseReady,
          ),
        );
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        _safeEmit(
          state.copyWith(status: StateStatus.failed, failureType: type),
        );
    }
  }

  Future<void> sendMessage(String text) async {
    if (state.conversationId == null) return;

    // Cancel any previous in-flight stream before starting a new one.
    await _streamSubscription?.cancel();
    _streamSubscription = null;

    final userMsg = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      text: text,
      isUser: true,
      timestamp: DateTime.now(),
    );

    final streamingId = 'stream_${DateTime.now().millisecondsSinceEpoch}';

    _safeEmit(
      state.copyWith(
        messages: [...state.messages, userMsg],
        isSending: true,
        streamingMessageId: streamingId,
        clearStreamingStatus: true,
        clearStage: true,
      ),
    );

    final stream = _repository.streamMessage(
      conversationId: state.conversationId!,
      message: text,
      ragConfig: state.chatMode.ragConfig,
      mode: state.isCaseChat ? 'case_intake' : 'chat',
      caseContext: state.attachedCaseContext,
      caseFileId: state.caseFileId,
    );

    final toolResultsCollected = <ToolResultData>[];
    final completer = Completer<void>();

    void emitConnectionError() {
      final errorMsg = ChatMessage(
        id: 'error_${DateTime.now().millisecondsSinceEpoch}',
        text: 'Connection error',
        isUser: false,
        timestamp: DateTime.now(),
        isError: true,
        failureType: ConsultationFailureType.network,
      );
      final msgs = List<ChatMessage>.from(state.messages)
        ..removeWhere((m) => m.id == streamingId);
      _safeEmit(
        state.copyWith(
          messages: [...msgs, errorMsg],
          isSending: false,
          clearStreamingStatus: true,
          clearStage: true,
          clearStreamingMessageId: true,
        ),
      );
    }

    _streamSubscription = stream.listen(
      (event) {
        if (isClosed) return;
        final type = event['type'];
        if (type == 'stage') {
          // Real pipeline position, reported live by the backend. It replaces
          // `streamingStatus` rather than sitting beside it: two competing
          // progress lines is worse than one, and the stage carries strictly
          // more (name + concrete detail + position).
          _safeEmit(
            state.copyWith(
              stage: PipelineStage.fromMap(Map<String, dynamic>.from(event)),
              clearStreamingStatus: true,
            ),
          );
        } else if (type == 'status') {
          // Legacy coarse status, still sent around the edges of the pipeline
          // (before the guardrail, during case build). Never overwrite a real
          // stage with it — the stage is the better signal once it exists.
          if (state.stage == null) {
            _safeEmit(
              state.copyWith(streamingStatus: event['message']?.toString()),
            );
          }
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
            _safeEmit(
              state.copyWith(
                messages: msgs,
                clearStreamingStatus: true,
                clearStage: true,
                isSending: false,
              ),
            );
          } else {
            final aiMsg = ChatMessage(
              id: streamingId,
              text: event['content']?.toString() ?? '',
              isUser: false,
              timestamp: DateTime.now(),
            );
            msgs.add(aiMsg);
            _safeEmit(
              state.copyWith(
                messages: msgs,
                clearStreamingStatus: true,
                clearStage: true,
                isSending: false,
              ),
            );
          }
        } else if (type == 'tool_executed') {
          final toolName = event['tool']?.toString() ?? '';
          final toolResult = (event['result'] as Map<String, dynamic>?) ?? {};

          toolResultsCollected.add(
            ToolResultData(
              toolName: toolName,
              status: event['status']?.toString() ?? 'executed',
              result: toolResult,
            ),
          );

          if (toolName == 'create_case' &&
              toolResult.containsKey('case_file_id')) {
            _safeEmit(
              state.copyWith(
                caseFileId: toolResult['case_file_id']?.toString(),
                // M11b: the 📁/🔧 prefixes are DROPPED. `streamingStatus` is a
                // STATE string rendered as bare `bodyS` beside the animated
                // typing dots — there is no icon slot to move a glyph into, and
                // plumbing an IconData through the cubit would put presentation
                // in the state layer. The dots already say "working"; the tool
                // name already says what. Both branches now read identically,
                // which is correct: they never were two kinds of progress.
                streamingStatus: _toolNameKa(toolName),
              ),
            );
          } else {
            _safeEmit(state.copyWith(streamingStatus: _toolNameKa(toolName)));
          }
        } else if (type == 'confirmation_required') {
          final pending = ToolResultData(
            toolName: event['tool_name']?.toString() ?? '',
            status: 'pending_confirmation',
            requiresConfirmation: true,
            confirmationId: event['confirmation_id']?.toString(),
            description: event['description']?.toString(),
          );
          toolResultsCollected.add(pending);
          _safeEmit(
            state.copyWith(
              pendingConfirmations: [...state.pendingConfirmations, pending],
            ),
          );
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
              toolResults: toolResultsCollected.isNotEmpty
                  ? toolResultsCollected
                  : null,
            );
          } else {
            final aiMsg = ChatMessage(
              id: streamingId,
              text: event['full_response']?.toString() ?? '',
              isUser: false,
              timestamp: DateTime.now(),
              citations: _parseChatCitations(event['citations']),
              trustLevel: event['trust_level']?.toString(),
              toolResults: toolResultsCollected.isNotEmpty
                  ? toolResultsCollected
                  : null,
            );
            msgs.add(aiMsg);
          }
          // Check done-event tool_results for case creation
          final doneToolResults = event['tool_results'] as List<dynamic>? ?? [];
          String? createdCaseId;
          for (final t in doneToolResults) {
            final map = t as Map<String, dynamic>;
            if (map['tool_name'] == 'create_case') {
              final result = map['result'] as Map<String, dynamic>? ?? {};
              createdCaseId = result['case_file_id']?.toString();
            }
          }

          final caseReady = event['case_analysis_ready'] == true;
          if (caseReady) {
            msgs.add(
              ChatMessage(
                id: 'case_ready_${DateTime.now().millisecondsSinceEpoch}',
                // M11b: emoji dropped — this renders as a chat BUBBLE, and the
                // bubble has no icon slot. The sentence already states success.
                text:
                    'საქმის სრული ანალიზი მომზადდა. დააჭირეთ "გენერაცია" ღილაკს საქმის შესაქმნელად.',
                isUser: false,
                timestamp: DateTime.now(),
              ),
            );
          }

          _safeEmit(
            state.copyWith(
              messages: msgs,
              isSending: false,
              clearStreamingStatus: true,
              clearStage: true,
              clearStreamingMessageId: true,
              caseAnalysisReady: caseReady,
              caseFileId: createdCaseId ?? state.caseFileId,
            ),
          );
          if (!completer.isCompleted) completer.complete();
        } else if (type == 'error') {
          final errorMsg = ChatMessage(
            id: 'error_${DateTime.now().millisecondsSinceEpoch}',
            text: event['message']?.toString() ?? 'An error occurred',
            isUser: false,
            timestamp: DateTime.now(),
            isError: true,
            failureType: ConsultationFailureType.unknown,
          );

          final msgs = List<ChatMessage>.from(state.messages)
            ..removeWhere((m) => m.id == streamingId);

          _safeEmit(
            state.copyWith(
              messages: [...msgs, errorMsg],
              isSending: false,
              clearStreamingStatus: true,
              clearStage: true,
              clearStreamingMessageId: true,
            ),
          );
          if (!completer.isCompleted) completer.complete();
        }
      },
      onError: (Object e) {
        emitConnectionError();
        if (!completer.isCompleted) completer.complete();
      },
      onDone: () {
        // Stream closed without an explicit done/error event (e.g. socket
        // dropped mid-response). If we're still showing the typing indicator,
        // surface a connection error rather than spinning forever.
        if (!isClosed && state.isSending) {
          emitConnectionError();
        }
        if (!completer.isCompleted) completer.complete();
      },
      cancelOnError: true,
    );

    await completer.future;
  }

  String _toolNameKa(String name) => switch (name) {
    'add_fact' => 'ფაქტი დამატებულია',
    'edit_fact' => 'ფაქტი განახლდა',
    'delete_fact' => 'ფაქტი წაშლილია',
    'add_argument' => 'არგუმენტი დამატებულია',
    'delete_argument' => 'არგუმენტი წაშლილია',
    'link_article' => 'მუხლი მიბმულია',
    'set_strategy' => 'სტრატეგია დაყენებულია',
    'add_action_item' => 'დავალება დამატებულია',
    'add_risk' => 'რისკი დამატებულია',
    'get_case_summary' => 'საქმის მიმოხილვა',
    'create_case' => 'საქმე შეიქმნა',
    'build_case_analysis' => 'სრული ანალიზი მზადდება',
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
        _safeEmit(state.copyWith(isBuildingCase: false, caseFileData: data));
        return data;
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        _safeEmit(state.copyWith(isBuildingCase: false, failureType: type));
        return null;
    }
  }

  /// Fetch the conversation history. Exposed so views can show history without
  /// constructing a throwaway repository (keeps DI in one place).
  Future<ConsultationResult<List<dynamic>>> fetchConversations() =>
      _repository.getConversations();

  void switchMode(ChatMode mode) => emit(state.copyWith(chatMode: mode));

  void attachCase({
    required String caseId,
    required String caseTitle,
    required String caseContext,
  }) {
    emit(
      state.copyWith(
        attachedCaseId: caseId,
        attachedCaseTitle: caseTitle,
        attachedCaseContext: caseContext,
      ),
    );
  }

  void detachCase() {
    emit(
      state.copyWith(
        clearAttachedCase: true,
      ),
    );
  }

  void injectMessage(ChatMessage message) {
    emit(
      state.copyWith(
        messages: [...state.messages, message],
      ),
    );
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
      text: text,
      isUser: true,
      timestamp: DateTime.now(),
    );
    _safeEmit(
      state.copyWith(messages: [...state.messages, userMsg], isSending: true),
    );

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
          id:
              data['id']?.toString() ??
              DateTime.now().millisecondsSinceEpoch.toString(),
          text: data['response']?.toString() ?? '',
          isUser: false,
          timestamp: DateTime.now(),
          citations: _parseChatCitations(data['citations']),
          toolResults: toolResults,
        );
        _safeEmit(
          state.copyWith(
            messages: [...state.messages, aiMsg],
            isSending: false,
            pendingConfirmations: [
              ...state.pendingConfirmations,
              ...pendingOnes,
            ],
          ),
        );
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        final errorMsg = ChatMessage(
          id: 'error_${DateTime.now().millisecondsSinceEpoch}',
          text: type.name,
          isUser: false,
          timestamp: DateTime.now(),
          isError: true,
          failureType: type,
        );
        _safeEmit(
          state.copyWith(
            messages: [...state.messages, errorMsg],
            isSending: false,
          ),
        );
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
          text: '${data['tool_name']}: შესრულდა',
          isUser: false,
          timestamp: DateTime.now(),
        );
        _safeEmit(
          state.copyWith(
            messages: [...state.messages, confirmMsg],
            pendingConfirmations: updatedPending,
          ),
        );
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        // Surface the failure instead of silently leaving the card on screen.
        final errorMsg = ChatMessage(
          id: 'error_${DateTime.now().millisecondsSinceEpoch}',
          text: 'მოქმედების დადასტურება ვერ მოხერხდა, სცადეთ ხელახლა',
          isUser: false,
          timestamp: DateTime.now(),
          isError: true,
          failureType: type,
        );
        _safeEmit(state.copyWith(messages: [...state.messages, errorMsg]));
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
          text: '${data['tool_name']}: გაუქმებულია',
          isUser: false,
          timestamp: DateTime.now(),
        );
        _safeEmit(
          state.copyWith(
            messages: [...state.messages, rejectMsg],
            pendingConfirmations: updatedPending,
          ),
        );
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        final errorMsg = ChatMessage(
          id: 'error_${DateTime.now().millisecondsSinceEpoch}',
          text: 'მოქმედების გაუქმება ვერ მოხერხდა, სცადეთ ხელახლა',
          isUser: false,
          timestamp: DateTime.now(),
          isError: true,
          failureType: type,
        );
        _safeEmit(state.copyWith(messages: [...state.messages, errorMsg]));
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
        url: map['article_url']?.toString() ?? map['source_url']?.toString(),
      );
    }).toList();
  }

  List<CitationData>? _parseChatCitations(dynamic raw) {
    if (raw is! List) return null;
    return raw.map((c) {
      final map = c as Map<String, dynamic>;
      return CitationData(
        articleId:
            map['article_number']?.toString() ??
            map['article_id']?.toString() ??
            '',
        articleTitle:
            map['raw_text']?.toString() ??
            map['article_title']?.toString() ??
            '',
        codeTitle:
            map['code_name']?.toString() ?? map['code_title']?.toString() ?? '',
        snippet:
            map['citation_text']?.toString() ??
            map['snippet']?.toString() ??
            '',
        trustLevel: map['verified'] == true ? 'verified' : 'guidance',
        url: map['article_url']?.toString() ?? map['source_url']?.toString(),
      );
    }).toList();
  }

  void reset() {
    emit(
      ConsultationState(chatMode: state.chatMode, isCaseChat: state.isCaseChat),
    );
  }
}
