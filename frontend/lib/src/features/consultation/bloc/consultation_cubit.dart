import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

part 'consultation_state.dart';

/// Manages AI consultation chat state: conversation lifecycle + messages.
/// Emits typed failure states — UI handles presentation.
class ConsultationCubit extends Cubit<ConsultationState> {
  final ConsultationRepository _repository;

  ConsultationCubit({required ConsultationRepository repository})
    : _repository = repository,
      super(const ConsultationState());

  /// Start or load a conversation linked to a case.
  Future<void> startConversation({String? caseId}) async {
    emit(state.copyWith(status: StateStatus.loading));

    final result = await _repository.createConversation(caseId: caseId);
    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        final conversationId = data['id'] as String? ?? '';
        emit(
          state.copyWith(
            status: StateStatus.success,
            conversationId: conversationId,
            messages: [],
          ),
        );
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        emit(state.copyWith(status: StateStatus.failed, failureType: type));
    }
  }

  /// Load existing conversation with messages.
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

        emit(state.copyWith(status: StateStatus.success, messages: messages));
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        emit(state.copyWith(status: StateStatus.failed, failureType: type));
    }
  }

  /// Send a user message → receive AI response.
  Future<void> sendMessage(String text) async {
    if (state.conversationId == null) return;

    // Add user message optimistically
    final userMsg = ChatMessage(
      id: DateTime.now().millisecondsSinceEpoch.toString(),
      text: text,
      isUser: true,
      timestamp: DateTime.now(),
    );
    emit(state.copyWith(messages: [...state.messages, userMsg], isSending: true));

    final result = await _repository.sendMessage(
      conversationId: state.conversationId!,
      message: text,
    );

    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        final aiMsg = ChatMessage(
          id: data['id']?.toString() ?? DateTime.now().millisecondsSinceEpoch.toString(),
          text: data['content']?.toString() ?? '',
          isUser: false,
          timestamp: DateTime.tryParse(data['created_at']?.toString() ?? '') ?? DateTime.now(),
          citations: _parseCitations(data['citations']),
          trustLevel: data['trust_level']?.toString(),
        );
        emit(state.copyWith(messages: [...state.messages, aiMsg], isSending: false));
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        // Emit failure type as an error message in the chat stream
        final errorMsg = ChatMessage(
          id: 'error_${DateTime.now().millisecondsSinceEpoch}',
          text: type.name, // UI will map this to Georgian
          isUser: false,
          timestamp: DateTime.now(),
          isError: true,
          failureType: type,
        );
        emit(state.copyWith(messages: [...state.messages, errorMsg], isSending: false));
    }
  }

  List<CitationData>? _parseCitations(dynamic raw) {
    if (raw == null) return null;
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
}
