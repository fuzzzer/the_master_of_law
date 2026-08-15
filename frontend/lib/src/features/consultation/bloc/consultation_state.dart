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
  final List<ToolResultData>? toolResults;

  const ChatMessage({
    required this.id,
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.citations,
    this.trustLevel,
    this.isError = false,
    this.failureType,
    this.toolResults,
  });

  /// Internal protocol sentinel embedded by the backend in assistant text.
  static final _caseReadySentinel = RegExp(r'\s*\[CASE_READY\]\s*');

  /// Text safe for display: strips internal protocol tokens (e.g. the
  /// `[CASE_READY]` marker) so they never leak into the conversation UI.
  String get displayText => text.replaceAll(_caseReadySentinel, '').trimRight();
}

class ToolResultData {
  final String toolName;
  final String status;
  final Map<String, dynamic> result;
  final bool requiresConfirmation;
  final String? confirmationId;
  final String? description;

  const ToolResultData({
    required this.toolName,
    required this.status,
    this.result = const {},
    this.requiresConfirmation = false,
    this.confirmationId,
    this.description,
  });
}

/// One reported stage of the backend pipeline.
///
/// The backend answers in 30-120s and used to say only "…" for all of it. A
/// stage carries a name, an optional CONCRETE detail ("23 articles found")
/// and its position, so the indicator can show movement rather than just
/// motion.
class PipelineStage {
  /// Stable identifier — `guard`, `search`, `draft`, `verify`, …
  /// Match on this, never on [label], which is display text.
  final String key;
  final String label;
  final String? detail;
  final int index;
  final int total;

  const PipelineStage({
    required this.key,
    required this.label,
    required this.index,
    required this.total,
    this.detail,
  });

  factory PipelineStage.fromMap(Map<String, dynamic> map) => PipelineStage(
    key: map['key']?.toString() ?? '',
    label: map['label']?.toString() ?? '',
    detail: map['detail']?.toString(),
    index: (map['index'] as num?)?.toInt() ?? 0,
    total: (map['total'] as num?)?.toInt() ?? 1,
  );

  /// 0.0-1.0 through the declared stage list. Stages a request skips never
  /// fire, so this advances in uneven jumps — it is a position, not an ETA.
  double get progress => total <= 1 ? 0 : (index / (total - 1)).clamp(0.0, 1.0);

  @override
  bool operator ==(Object other) =>
      other is PipelineStage &&
      other.key == key &&
      other.detail == detail &&
      other.index == index;

  @override
  int get hashCode => Object.hash(key, detail, index);
}

class CitationData {
  final String articleId;
  final String articleTitle;
  final String codeTitle;
  final String snippet;
  final String trustLevel;
  final String? url;

  const CitationData({
    required this.articleId,
    required this.articleTitle,
    required this.codeTitle,
    required this.snippet,
    required this.trustLevel,
    this.url,
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
  final String? caseFileId;
  final List<ToolResultData> pendingConfirmations;
  final String? streamingStatus;
  final String? streamingMessageId;
  final PipelineStage? stage;

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
    this.caseFileId,
    this.pendingConfirmations = const [],
    this.streamingStatus,
    this.streamingMessageId,
    this.stage,
  });

  bool get hasCaseAttached => attachedCaseId != null;

  bool get isAgentMode => caseFileId != null;

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
    String? caseFileId,
    bool clearCaseFileId = false,
    List<ToolResultData>? pendingConfirmations,
    String? streamingStatus,
    bool clearStreamingStatus = false,
    String? streamingMessageId,
    bool clearStreamingMessageId = false,
    PipelineStage? stage,
    bool clearStage = false,
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
      attachedCaseId: clearAttachedCase
          ? null
          : (attachedCaseId ?? this.attachedCaseId),
      attachedCaseTitle: clearAttachedCase
          ? null
          : (attachedCaseTitle ?? this.attachedCaseTitle),
      attachedCaseContext: clearAttachedCase
          ? null
          : (attachedCaseContext ?? this.attachedCaseContext),
      caseFileId: clearCaseFileId ? null : (caseFileId ?? this.caseFileId),
      pendingConfirmations: pendingConfirmations ?? this.pendingConfirmations,
      streamingStatus: clearStreamingStatus
          ? null
          : (streamingStatus ?? this.streamingStatus),
      streamingMessageId: clearStreamingMessageId
          ? null
          : (streamingMessageId ?? this.streamingMessageId),
      stage: clearStage ? null : (stage ?? this.stage),
    );
  }
}
