enum FeedbackCategory {
  accuracy,
  completeness,
  relevance,
  formatting,
  citationQuality,
  legalReasoning,
  overall;

  String get apiValue => switch (this) {
        accuracy => 'accuracy',
        completeness => 'completeness',
        relevance => 'relevance',
        formatting => 'formatting',
        citationQuality => 'citation_quality',
        legalReasoning => 'legal_reasoning',
        overall => 'overall',
      };

  String get displayNameKa => switch (this) {
        accuracy => 'სიზუსტე',
        completeness => 'სრულყოფილება',
        relevance => 'რელევანტურობა',
        formatting => 'ფორმატირება',
        citationQuality => 'ციტატის ხარისხი',
        legalReasoning => 'სამართლებრივი მსჯელობა',
        overall => 'საერთო',
      };
}

enum FeedbackTargetType {
  caseFile,
  conversation;

  String get apiValue => switch (this) {
        caseFile => 'case_file',
        conversation => 'conversation',
      };
}

class FeedbackSubmitRequestParameters {
  final FeedbackTargetType targetType;
  final String targetId;
  final FeedbackCategory category;
  final int rating;
  final String? comment;
  final String? specificSection;

  const FeedbackSubmitRequestParameters({
    required this.targetType,
    required this.targetId,
    required this.category,
    required this.rating,
    this.comment,
    this.specificSection,
  });

  Map<String, dynamic> toMap() => {
        'target_type': targetType.apiValue,
        'target_id': targetId,
        'category': category.apiValue,
        'rating': rating,
        if (comment != null) 'comment': comment,
        if (specificSection != null) 'specific_section': specificSection,
      };
}

class FeedbackSubmitResponseData {
  final String id;
  final String createdAt;

  const FeedbackSubmitResponseData({required this.id, required this.createdAt});

  factory FeedbackSubmitResponseData.fromMap(Map<String, dynamic> map) => FeedbackSubmitResponseData(
        id: map['id'] as String,
        createdAt: map['created_at'] as String? ?? '',
      );
}
