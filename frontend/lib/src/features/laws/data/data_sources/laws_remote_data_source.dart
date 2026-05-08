import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:themasteroflaw/src/src.dart';

/// Remote data source for Laws browser API (all free endpoints).
class LawsRemoteDataSource {
  final ThemasteroflawHttpClient _httpClient;

  LawsRemoteDataSource()
      : _httpClient = sl.get<ThemasteroflawHttpClient>();

  Uri _uri(String path, [Map<String, String>? queryParams]) => Uri.parse(
        '${dotenv.env['API_BASE_URL'] ?? 'http://127.0.0.1:8000'}$path',
      ).replace(queryParameters: queryParams);

  /// GET /api/v1/laws/search?q=... — search across all laws.
  Future<LawSearchResults> searchLaws(String query, {int topK = 20}) async {
    final response = await _httpClient.get<Map<String, dynamic>>(
      _uri('/api/v1/laws/search', {'q': query, 'top_k': topK.toString()}),
    );
    return LawSearchResults.fromMap(response.data!);
  }

  /// GET /api/v1/laws/codes — list all legal codes.
  Future<List<LawCode>> getCodes() async {
    final response = await _httpClient.get<Map<String, dynamic>>(
      _uri('/api/v1/laws/codes'),
    );
    final rawCodes = response.data!['codes'] as List<dynamic>? ?? [];
    return rawCodes
        .map((c) => LawCode.fromMap(c as Map<String, dynamic>))
        .toList();
  }

  /// GET /api/v1/laws/codes/{id} — get code structure (chapters, articles).
  Future<Map<String, dynamic>> getCodeStructure(String codeId) async {
    final response = await _httpClient.get<Map<String, dynamic>>(
      _uri('/api/v1/laws/codes/$codeId'),
    );
    return response.data!;
  }

  /// GET /api/v1/laws/articles/{id} — get full article text.
  Future<LawArticleDetail> getArticle(String articleId) async {
    final response = await _httpClient.get<Map<String, dynamic>>(
      _uri('/api/v1/laws/articles/$articleId'),
    );
    return LawArticleDetail.fromMap(response.data!);
  }
}
