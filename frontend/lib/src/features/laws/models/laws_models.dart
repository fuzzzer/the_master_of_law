/// A Georgian legal code (e.g., Civil Code, Criminal Code).
class LawCode {
  final String id;
  final String titleKa;
  final String titleEn;
  final String? description;
  final int articleCount;

  const LawCode({
    required this.id,
    required this.titleKa,
    this.titleEn = '',
    this.description,
    this.articleCount = 0,
  });
}

/// A single article within a legal code.
class LawArticle {
  final String id;
  final String codeId;
  final String articleNumber;
  final String titleKa;
  final String contentKa;
  final String? chapter;

  const LawArticle({
    required this.id,
    required this.codeId,
    required this.articleNumber,
    required this.titleKa,
    required this.contentKa,
    this.chapter,
  });
}

/// Search result from the law corpus.
class LawSearchResult {
  final LawArticle article;
  final double relevanceScore;
  final String matchedSnippet;

  const LawSearchResult({
    required this.article,
    required this.relevanceScore,
    required this.matchedSnippet,
  });
}
