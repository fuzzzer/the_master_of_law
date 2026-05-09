import 'dart:convert';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class ConsultationRemoteDataSource {
  final ThemasteroflawHttpClient _httpClient;

  ConsultationRemoteDataSource() : _httpClient = sl.get<ThemasteroflawHttpClient>();

  Uri _uri(String path) => Uri.parse(
    '${dotenv.env['API_BASE_URL'] ?? 'http://127.0.0.1:8000'}$path',
  );

  Future<Map<String, dynamic>> createConversation({String? caseId}) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/conversations'),
      body: {if (caseId != null) 'case_id': caseId},
    );
    return response.data!;
  }

  Future<List<dynamic>> getConversations() async {
    final response = await _httpClient.get<Map<String, dynamic>>(_uri('/api/v1/conversations'));
    return (response.data!['conversations'] as List<dynamic>?) ?? [];
  }

  Future<Map<String, dynamic>> getConversation(String conversationId) async {
    final response = await _httpClient.get<Map<String, dynamic>>(
      _uri('/api/v1/conversations/$conversationId'),
    );
    return response.data!;
  }

  Future<void> deleteConversation(String conversationId) async {
    await _httpClient.delete<void>(_uri('/api/v1/conversations/$conversationId'));
  }

  Future<Map<String, dynamic>> sendMessage({
    required String conversationId,
    required String message,
    Map<String, dynamic>? ragConfig,
    String mode = 'chat',
    String? caseContext,
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/chat/$conversationId/send'),
      body: {
        'message': message,
        if (ragConfig != null) 'rag_config': ragConfig,
        'mode': mode,
        if (caseContext != null) 'case_context': caseContext,
      },
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> buildCaseFile({
    required String conversationId,
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/case-files/build'),
      body: {'conversation_id': conversationId},
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> sendAgentMessage({
    required String conversationId,
    required String message,
    required String caseFileId,
    Map<String, dynamic>? ragConfig,
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/chat/$conversationId/agent'),
      body: {
        'message': message,
        'mode': 'case_agent',
        'case_file_id': caseFileId,
        if (ragConfig != null) 'rag_config': ragConfig,
      },
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> confirmToolAction({
    required String conversationId,
    required String confirmationId,
    required bool confirmed,
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/chat/$conversationId/confirm-tool'),
      body: {
        'confirmation_id': confirmationId,
        'confirmed': confirmed,
      },
    );
    return response.data!;
  }

  Future<List<dynamic>> listCaseFiles() async {
    final response = await _httpClient.get<Map<String, dynamic>>(
      _uri('/api/v1/case-files'),
    );
    return (response.data!['case_files'] as List<dynamic>?) ?? [];
  }

  Stream<Map<String, dynamic>> streamMessage({
    required String conversationId,
    required String message,
    Map<String, dynamic>? ragConfig,
    String mode = 'chat',
    String? caseContext,
  }) async* {
    final baseUrl = dotenv.env['API_BASE_URL'] ?? 'http://127.0.0.1:8000';
    final wsUrl = baseUrl.replaceFirst('http://', 'ws://').replaceFirst('https://', 'wss://');
    final uri = Uri.parse('$wsUrl/api/v1/chat/$conversationId/ws');
    
    final channel = WebSocketChannel.connect(uri);
    
    // Send initial message
    channel.sink.add(jsonEncode({
      'message': message,
      if (ragConfig != null) 'rag_config': ragConfig,
      'mode': mode,
      if (caseContext != null) 'case_context': caseContext,
    }));
    
    try {
      await for (final data in channel.stream) {
        final decoded = jsonDecode(data as String) as Map<String, dynamic>;
        yield decoded;
        if (decoded['type'] == 'done' || decoded['type'] == 'error') {
          break;
        }
      }
    } finally {
      channel.sink.close();
    }
  }
}
