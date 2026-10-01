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

  /// What the backend's `/articles/{id}` resolves: the chunk id without its
  /// `.chunk_N` suffix (e.g. `admin_offences_code.article_1`). The human
  /// label in [articleNumber] ("მუხლი 1") is never an id.
  String get articleId => chunkId.split('.chunk_').first;

  /// The article's text alone. Each chunk in the corpus is wrapped for
  /// embedding: a header line ("code | (#n) | chapter | article | title"), a
  /// "წყარო:" line, then the body, then a one-line disclaimer. The screens
  /// show the code, number and title themselves, so the wrapper is noise.
  String get bodyText {
    var text = content.trim();
    final firstBreak = text.indexOf('\n\n');
    if (firstBreak > 0 && text.substring(0, firstBreak).contains(' | ')) {
      text = text.substring(firstBreak + 2);
    }
    final lastBreak = text.lastIndexOf('\n\n');
    if (lastBreak > 0 &&
        text
            .substring(lastBreak)
            .contains('მხოლოდ საინფორმაციო მიზნებისთვის')) {
      text = text.substring(0, lastBreak);
    }
    return text.trim();
  }

  String get codeName => metadata['code_name']?.toString() ?? '';

  /// Human label, already prefixed by the corpus: "მუხლი 1".
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

  String get combinedContent => chunks.map((c) => c.bodyText).join('\n\n');
  String get codeName => chunks.isNotEmpty ? chunks.first.codeName : '';
  String get articleNumber =>
      chunks.isNotEmpty ? chunks.first.articleNumber : '';
  String get articleTitle => chunks.isNotEmpty ? chunks.first.articleTitle : '';
}
