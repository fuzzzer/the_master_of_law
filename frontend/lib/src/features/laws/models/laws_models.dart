/// A Georgian legal code (e.g., Civil Code, Criminal Code).
class LawCode {
  final String id;
  final String name;
  final int articleCount;
  final String sourceUrl;

  const LawCode({
    required this.id,
    required this.name,
    this.articleCount = 0,
    this.sourceUrl = '',
  });

  factory LawCode.fromMap(Map<String, dynamic> map) {
    return LawCode(
      id: map['code_id']?.toString() ?? '',
      name: map['name']?.toString() ?? '',
      articleCount: map['article_count'] as int? ?? 0,
      sourceUrl: map['source_url']?.toString() ?? '',
    );
  }
}

/// A single chunk from the law corpus (search result or article content).
class LawChunk {
  final String chunkId;
  final String content;
  final Map<String, dynamic> metadata;

  const LawChunk({
    required this.chunkId,
    required this.content,
    this.metadata = const {},
  });

  factory LawChunk.fromMap(Map<String, dynamic> map) {
    return LawChunk(
      chunkId: map['chunk_id']?.toString() ?? '',
      content: map['content']?.toString() ?? '',
      metadata: map['metadata'] as Map<String, dynamic>? ?? {},
    );
  }

  String get codeName => metadata['code_name']?.toString() ?? '';
  String get articleNumber => metadata['article_number']?.toString() ?? '';
  String get articleTitle => metadata['article_title']?.toString() ?? '';
  String get citationText => metadata['citation_text']?.toString() ?? '';
  String get articleUrl => metadata['article_url']?.toString() ?? '';
}

/// Search results from the law corpus.
class LawSearchResults {
  final List<LawChunk> results;
  final String query;
  final int total;

  const LawSearchResults({
    required this.results,
    required this.query,
    required this.total,
  });

  factory LawSearchResults.fromMap(Map<String, dynamic> map) {
    final rawResults = map['results'] as List<dynamic>? ?? [];
    return LawSearchResults(
      results: rawResults
          .map((r) => LawChunk.fromMap(r as Map<String, dynamic>))
          .toList(),
      query: map['query']?.toString() ?? '',
      total: map['total'] as int? ?? 0,
    );
  }
}

/// Article detail (all chunks for a single article).
class LawArticleDetail {
  final String articleId;
  final List<LawChunk> chunks;
  final int total;

  const LawArticleDetail({
    required this.articleId,
    required this.chunks,
    required this.total,
  });

  factory LawArticleDetail.fromMap(Map<String, dynamic> map) {
    final rawChunks = map['chunks'] as List<dynamic>? ?? [];
    return LawArticleDetail(
      articleId: map['article_id']?.toString() ?? '',
      chunks: rawChunks
          .map((c) => LawChunk.fromMap(c as Map<String, dynamic>))
          .toList(),
      total: map['total'] as int? ?? 0,
    );
  }

  String get combinedContent => chunks.map((c) => c.content).join('\n\n');
  String get codeName => chunks.isNotEmpty ? chunks.first.codeName : '';
  String get articleNumber => chunks.isNotEmpty ? chunks.first.articleNumber : '';
  String get articleTitle => chunks.isNotEmpty ? chunks.first.articleTitle : '';
}
