import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:themasteroflaw/src/src.dart';

/// Remote data source for AI chat API endpoints.
/// Uses `sl.get<ThemasteroflawHttpClient>()` per data-source convention.
class ConsultationRemoteDataSource {
  final ThemasteroflawHttpClient _httpClient;

  ConsultationRemoteDataSource() : _httpClient = sl.get<ThemasteroflawHttpClient>();

  Uri _uri(String path) => Uri.parse(
    '${dotenv.env['API_BASE_URL'] ?? 'http://127.0.0.1:8000'}$path',
  );

  /// POST /api/v1/conversations — create new conversation.
  Future<Map<String, dynamic>> createConversation({String? caseId}) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/conversations'),
      body: {
        if (caseId != null) 'case_id': caseId,
      },
    );
    return response.data!;
  }

  /// GET /api/v1/conversations — list user's conversations.
  Future<List<dynamic>> getConversations() async {
    final response = await _httpClient.get<List<dynamic>>(
      _uri('/api/v1/conversations'),
    );
    return response.data!;
  }

  /// GET /api/v1/conversations/{id} — get conversation with messages.
  Future<Map<String, dynamic>> getConversation(String conversationId) async {
    final response = await _httpClient.get<Map<String, dynamic>>(
      _uri('/api/v1/conversations/$conversationId'),
    );
    return response.data!;
  }

  /// DELETE /api/v1/conversations/{id} — delete conversation.
  Future<void> deleteConversation(String conversationId) async {
    await _httpClient.delete<void>(
      _uri('/api/v1/conversations/$conversationId'),
    );
  }

  /// POST /api/v1/chat/{id}/send — send message, get AI response (1 credit).
  Future<Map<String, dynamic>> sendMessage({
    required String conversationId,
    required String message,
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/chat/$conversationId/send'),
      body: {'message': message},
    );
    return response.data!;
  }
}
