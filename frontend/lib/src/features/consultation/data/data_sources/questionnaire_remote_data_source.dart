import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:fuzzzy_law/src/src.dart';

class QuestionnaireRemoteDataSource {
  final FuzzzyLawHttpClient _httpClient;

  QuestionnaireRemoteDataSource() : _httpClient = sl.get<FuzzzyLawHttpClient>();

  Uri _uri(String path) => Uri.parse(
    '${dotenv.env['API_BASE_URL'] ?? 'http://127.0.0.1:8000'}$path',
  );

  Future<Map<String, dynamic>> generateQuestionnaire({
    required String conversationId,
    required String domain,
    required String userDescription,
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/questionnaire/$conversationId/generate'),
      body: {'domain': domain, 'user_description': userDescription},
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> getQuestionnaire(String conversationId) async {
    final response = await _httpClient.get<Map<String, dynamic>>(
      _uri('/api/v1/questionnaire/$conversationId'),
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> submitAnswer({
    required String conversationId,
    required String questionId,
    required String answer,
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/questionnaire/$conversationId/answer'),
      body: {'question_id': questionId, 'answer': answer},
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> skipRemaining(String conversationId) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/questionnaire/$conversationId/skip'),
      body: {},
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> extractFromNarrative({
    required String conversationId,
    required String domain,
    required String narrative,
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/questionnaire/$conversationId/extract'),
      body: {'domain': domain, 'narrative': narrative},
    );
    return response.data!;
  }
}
