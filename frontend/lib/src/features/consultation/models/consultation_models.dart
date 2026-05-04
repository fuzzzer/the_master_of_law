/// Chat message model for AI consultation.
class ConsultationMessage {
  final String id;
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final List<LawCitation>? citations;

  const ConsultationMessage({
    required this.id,
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.citations,
  });
}

/// Citation from the legal corpus.
class LawCitation {
  final String articleId;
  final String articleTitle;
  final String codeTitle;
  final String snippet;
  final String trustLevel; // verified, interpretation, guidance

  const LawCitation({
    required this.articleId,
    required this.articleTitle,
    required this.codeTitle,
    required this.snippet,
    required this.trustLevel,
  });
}
