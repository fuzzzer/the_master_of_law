import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:themasteroflaw/src/src.dart';

/// Remote data source for questionnaire API endpoints.
class QuestionnaireRemoteDataSource {
  final ThemasteroflawHttpClient _httpClient;

  QuestionnaireRemoteDataSource() : _httpClient = sl.get<ThemasteroflawHttpClient>();

  Uri _uri(String path) => Uri.parse(
    '${dotenv.env['API_BASE_URL'] ?? 'http://127.0.0.1:8000'}$path',
  );

  /// POST /api/v1/questionnaire/{conversation_id}/generate
  Future<Map<String, dynamic>> generateQuestionnaire({
    required String conversationId,
    required String domain,
    String context = '',
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/questionnaire/$conversationId/generate'),
      body: {
        'domain': domain,
        'context': context,
      },
    );
    return response.data!;
  }

  /// GET /api/v1/questionnaire/{conversation_id}
  Future<Map<String, dynamic>> getQuestionnaire(String conversationId) async {
    final response = await _httpClient.get<Map<String, dynamic>>(
      _uri('/api/v1/questionnaire/$conversationId'),
    );
    return response.data!;
  }

  /// POST /api/v1/questionnaire/{conversation_id}/answer
  Future<Map<String, dynamic>> submitAnswer({
    required String conversationId,
    required String questionId,
    required String answer,
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/questionnaire/$conversationId/answer'),
      body: {
        'question_id': questionId,
        'answer': answer,
      },
    );
    return response.data!;
  }

  /// POST /api/v1/questionnaire/{conversation_id}/skip
  Future<Map<String, dynamic>> skipQuestion({
    required String conversationId,
    required String questionId,
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/questionnaire/$conversationId/skip'),
      body: {
        'question_id': questionId,
      },
    );
    return response.data!;
  }
}
