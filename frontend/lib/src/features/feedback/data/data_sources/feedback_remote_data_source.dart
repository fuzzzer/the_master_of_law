import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:themasteroflaw/src/src.dart';

class FeedbackRemoteDataSource {
  final ThemasteroflawHttpClient _httpClient;

  FeedbackRemoteDataSource() : _httpClient = sl.get<ThemasteroflawHttpClient>();

  Uri _uri(String path) => Uri.parse(
    '${dotenv.env['API_BASE_URL'] ?? 'http://127.0.0.1:8000'}$path',
  );

  Future<Map<String, dynamic>> submitFeedback(FeedbackSubmitRequestParameters params) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/feedback'),
      body: params.toMap(),
    );
    return response.data!;
  }
}
