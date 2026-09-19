import 'dart:convert';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

class ConsultationRemoteDataSource {
  final FuzzzyLawHttpClient _httpClient;

  ConsultationRemoteDataSource() : _httpClient = sl.get<FuzzzyLawHttpClient>();

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
      options: longRunningRequest(),
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> buildCaseFile({
    required String conversationId,
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/case-files/build'),
      body: {'conversation_id': conversationId},
      options: longRunningRequest(),
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
      options: longRunningRequest(),
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
    String? caseFileId,
  }) async* {
    final baseUrl = dotenv.env['API_BASE_URL'] ?? 'http://127.0.0.1:8000';
    final wsUrl = baseUrl.replaceFirst('http://', 'ws://').replaceFirst('https://', 'wss://');

    final secureStorage = sl.get<SecureStorageService>();
    final apiKey = await secureStorage.getData('temporary_api_key');
    final deviceId = await sl.get<DeviceIdService>().get();

    // Browsers cannot set headers on a WebSocket handshake, so what the auth
    // interceptor sends as headers has to travel in the query string here.
    // Uri handles the escaping; string interpolation would corrupt any key
    // containing a reserved character.
    final uri = Uri.parse('$wsUrl/api/v1/chat/$conversationId/ws').replace(
      queryParameters: <String, String>{
        if (apiKey != null && apiKey.isNotEmpty) 'api_key': apiKey,
        'device_id': deviceId,
        ...sl.get<ModelPreferenceService>().queryParameters,
      },
    );
    
    final channel = WebSocketChannel.connect(uri);

    try {
      // Surface handshake failures (server down / bad upgrade) explicitly rather
      // than waiting for the stream to error far downstream.
      await channel.ready.timeout(const Duration(seconds: 15));

      // Send initial message
      channel.sink.add(jsonEncode({
        'message': message,
        if (ragConfig != null) 'rag_config': ragConfig,
        'mode': mode,
        if (caseContext != null) 'case_context': caseContext,
        if (caseFileId != null) 'case_file_id': caseFileId,
      }));

      // Per-message inactivity timeout: if the server never sends another
      // frame (and no done/error), don't let the typing indicator spin forever.
      final guarded = channel.stream.timeout(
        const Duration(seconds: 60),
        onTimeout: (sink) {
          sink.add(jsonEncode({'type': 'error', 'message': 'timeout'}));
          sink.close();
        },
      );

      await for (final data in guarded) {
        final decoded = jsonDecode(data as String) as Map<String, dynamic>;
        yield decoded;
        if (decoded['type'] == 'done' || decoded['type'] == 'error') {
          break;
        }
      }
    } finally {
      await channel.sink.close();
    }
  }
}
