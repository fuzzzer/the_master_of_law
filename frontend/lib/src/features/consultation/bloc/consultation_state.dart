part of 'consultation_cubit.dart';

class ChatMessage {
  final String id;
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final List<CitationData>? citations;
  final String? trustLevel;
  final bool isError;
  final ConsultationFailureType? failureType;

  const ChatMessage({
    required this.id,
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.citations,
    this.trustLevel,
    this.isError = false,
    this.failureType,
  });
}

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
  final ConsultationFailureType? failureType;
  final ChatMode chatMode;
  final bool isCaseChat;
  final bool caseAnalysisReady;
  final bool isBuildingCase;
  final Map<String, dynamic>? caseFileData;
  final String? attachedCaseId;
  final String? attachedCaseTitle;
  final String? attachedCaseContext;

  const ConsultationState({
    this.status = StateStatus.initial,
    this.conversationId,
    this.messages = const [],
    this.isSending = false,
    this.failureType,
    this.chatMode = ChatMode.allSources,
    this.isCaseChat = false,
    this.caseAnalysisReady = false,
    this.isBuildingCase = false,
    this.caseFileData,
    this.attachedCaseId,
    this.attachedCaseTitle,
    this.attachedCaseContext,
  });

  bool get hasCaseAttached => attachedCaseId != null;

  ConsultationState copyWith({
    StateStatus? status,
    String? conversationId,
    List<ChatMessage>? messages,
    bool? isSending,
    ConsultationFailureType? failureType,
    ChatMode? chatMode,
    bool? isCaseChat,
    bool? caseAnalysisReady,
    bool? isBuildingCase,
    Map<String, dynamic>? caseFileData,
    String? attachedCaseId,
    String? attachedCaseTitle,
    String? attachedCaseContext,
    bool clearAttachedCase = false,
  }) {
    return ConsultationState(
      status: status ?? this.status,
      conversationId: conversationId ?? this.conversationId,
      messages: messages ?? this.messages,
      isSending: isSending ?? this.isSending,
      failureType: failureType ?? this.failureType,
      chatMode: chatMode ?? this.chatMode,
      isCaseChat: isCaseChat ?? this.isCaseChat,
      caseAnalysisReady: caseAnalysisReady ?? this.caseAnalysisReady,
      isBuildingCase: isBuildingCase ?? this.isBuildingCase,
      caseFileData: caseFileData ?? this.caseFileData,
      attachedCaseId: clearAttachedCase ? null : (attachedCaseId ?? this.attachedCaseId),
      attachedCaseTitle: clearAttachedCase ? null : (attachedCaseTitle ?? this.attachedCaseTitle),
      attachedCaseContext: clearAttachedCase ? null : (attachedCaseContext ?? this.attachedCaseContext),
    );
  }
}
