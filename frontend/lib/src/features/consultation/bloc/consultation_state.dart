part of 'consultation_cubit.dart';

/// Single chat message (user or AI).
class ChatMessage {
  final String id;
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final List<CitationData>? citations;
  final String? trustLevel;
  final bool isError;

  const ChatMessage({
    required this.id,
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.citations,
    this.trustLevel,
    this.isError = false,
  });
}

/// Parsed citation from AI response.
class CitationData {
  final String articleId;
  final String articleTitle;
  final String codeTitle;
  final String snippet;
  final String trustLevel;

  const CitationData({
    required this.articleId,
    required this.articleTitle,
    required this.codeTitle,
    required this.snippet,
    required this.trustLevel,
  });
}

class ConsultationState {
  final StateStatus status;
  final String? conversationId;
  final List<ChatMessage> messages;
  final bool isSending;
  final String? errorMessage;

  const ConsultationState({
    this.status = StateStatus.initial,
    this.conversationId,
    this.messages = const [],
    this.isSending = false,
    this.errorMessage,
  });

  ConsultationState copyWith({
    StateStatus? status,
    String? conversationId,
    List<ChatMessage>? messages,
    bool? isSending,
    String? errorMessage,
  }) {
    return ConsultationState(
      status: status ?? this.status,
      conversationId: conversationId ?? this.conversationId,
      messages: messages ?? this.messages,
      isSending: isSending ?? this.isSending,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}
