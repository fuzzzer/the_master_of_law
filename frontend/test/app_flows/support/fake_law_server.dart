import 'dart:convert';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:package_info_plus/package_info_plus.dart';

/// The backend as the app sees it over HTTP, answered in memory.
///
/// It plugs in below Dio, so the app's own interceptors still run: the stored
/// key still travels as `X-API-Key`, and a 401 still clears it and signals the
/// router, exactly as against the real server.
class FakeLawServer implements HttpClientAdapter {
  static const baseUrl = 'http://fake-law-api.test';

  /// What Google accepts in this fake: the shape of an AI Studio key.
  static final _aiStudioKey = RegExp(r'^AIza[0-9A-Za-z_\-]{35}$');

  final requests = <RequestOptions>[];

  @override
  Future<ResponseBody> fetch(
    RequestOptions options,
    Stream<Uint8List>? requestStream,
    Future<void>? cancelFuture,
  ) async {
    requests.add(options);
    final (status, body) = _answer(options);
    return ResponseBody.fromString(
      jsonEncode(body),
      status,
      headers: {
        Headers.contentTypeHeader: [Headers.jsonContentType],
      },
    );
  }

  (int, Map<String, dynamic>) _answer(RequestOptions options) {
    final route = '${options.method} ${options.uri.path}';
    return switch (route) {
      'GET /api/v1/api-keys/validate' => _validate(options),
      'GET /api/v1/account/credits' => (200, {'credits': 100}),
      'GET /api/v1/models' => (200, FakeLawData.models),
      'GET /api/v1/conversations' => (200, {'conversations': <Object>[]}),
      'POST /api/v1/conversations' => (200, {'id': FakeLawData.conversationId}),
      'GET /api/v1/laws/codes' => (200, FakeLawData.codes),
      'GET /api/v1/laws/codes/${FakeLawData.codeId}' => (
        200,
        FakeLawData.codeStructure,
      ),
      'GET /api/v1/laws/articles/${FakeLawData.articleId}' => (
        200,
        FakeLawData.article,
      ),
      _ => (404, {'error': 'not_found', 'message': route}),
    };
  }

  (int, Map<String, dynamic>) _validate(RequestOptions options) {
    final key = options.headers['X-API-Key']?.toString() ?? '';
    if (_aiStudioKey.hasMatch(key)) {
      return (200, {'valid': true, 'models_available': 3});
    }
    return (
      401,
      {
        'error': 'byok_key_invalid',
        'message': 'გასაღები არ მუშაობს.',
      },
    );
  }

  @override
  void close({bool force = false}) {}
}

/// The app's HTTP client with its real interceptors, talking to [server].
///
/// Each call mirrors [FuzzzyLawHttpClient]: Dio failures leave as the same
/// typed exceptions, so repositories and screens see what they see live.
class FakeServerHttpClient extends FuzzzyLawHttpClient {
  FakeServerHttpClient({
    required this.server,
    required PackageInfo packageInfo,
  }) : _dio = Dio(DefaultBaseOptions()),
       super(packageInfo: packageInfo) {
    _dio
      ..httpClientAdapter = server
      ..interceptors.addAll([
        FuzzzyLawApiInterceptor(packageInfo: packageInfo),
        FuzzzyLawAuthInterceptor(),
      ]);
  }

  final FakeLawServer server;
  final Dio _dio;

  Future<Response<T>> _send<T>(Future<Response<T>> Function() call) async {
    try {
      return await call();
    } on DioException catch (ex) {
      throw FuzzzyLawRestApiExceptionTranslator.translateToHttpClientException(
        ex,
      );
    }
  }

  @override
  Future<Response<T>> get<T>(
    Uri uri, {
    Options? options,
    CancelToken? cancelToken,
    void Function(int, int)? onReceiveProgress,
    bool throwExceptionOnFuzzzyLawUnsuccessfulResponse = true,
  }) => _send(() => _dio.getUri<T>(uri, options: options));

  @override
  Future<Response<T>> post<T>(
    Uri uri, {
    Object? body,
    Map<String, String>? headers,
    Options? options,
    CancelToken? cancelToken,
    void Function(int, int)? onSendProgress,
    void Function(int, int)? onReceiveProgress,
    bool handlesFuzzzyLawErrors = true,
  }) => _send(() => _dio.postUri<T>(uri, data: body, options: options));

  @override
  Future<Response<T>> put<T>(
    Uri uri, {
    Object? body,
    Map<String, String>? headers,
    Options? options,
    CancelToken? cancelToken,
    void Function(int, int)? onSendProgress,
    void Function(int, int)? onReceiveProgress,
  }) => _send(() => _dio.putUri<T>(uri, data: body, options: options));

  @override
  Future<Response<T>> patch<T>(
    Uri uri, {
    Object? body,
    Options? options,
    CancelToken? cancelToken,
    void Function(int, int)? onSendProgress,
    void Function(int, int)? onReceiveProgress,
  }) => _send(() => _dio.patchUri<T>(uri, data: body, options: options));

  @override
  Future<Response<T>> delete<T>(
    Uri uri, {
    Object? body,
    Options? options,
    CancelToken? cancelToken,
  }) => _send(() => _dio.deleteUri<T>(uri, data: body, options: options));
}

/// The chat socket, scripted: one answer streamed in two chunks, then done.
///
/// Only the socket is replaced; the conversation itself is still created over
/// HTTP through [FakeLawServer].
class ScriptedChatRemoteDataSource extends ConsultationRemoteDataSource {
  final sentMessages = <String>[];

  @override
  Stream<Map<String, dynamic>> streamMessage({
    required String conversationId,
    required String message,
    Map<String, dynamic>? ragConfig,
    String mode = 'chat',
    String? caseContext,
    String? caseFileId,
  }) async* {
    sentMessages.add(message);
    yield {'type': 'chunk', 'content': FakeLawData.answerStart};
    yield {'type': 'chunk', 'content': FakeLawData.answerEnd};
    yield {
      'type': 'done',
      'full_response': FakeLawData.answerStart + FakeLawData.answerEnd,
      'citations': <Object>[],
    };
  }
}

/// Canned server data, Georgian like the live corpus.
abstract final class FakeLawData {
  static const validKey = 'AIzaSyFakeKeyForAppFlowChecks_000000000';
  static const invalidKey = 'definitely-not-a-google-key';

  static const conversationId = 'conv-app-flow-1';

  static const codeId = 'civil_code';
  static const codeName = 'საქართველოს სამოქალაქო კოდექსი';
  static const articleId = 'civil_code.article_1';
  static const articleTitle =
      'სამოქალაქო კანონმდებლობით რეგულირებული ურთიერთობები';
  static const articleBody =
      'სამოქალაქო კანონმდებლობა აწესრიგებს კერძო ხასიათის ქონებრივ, '
      'საოჯახო და პირად ურთიერთობებს.';

  static const answerStart = 'სამოქალაქო კოდექსის პირველი მუხლის ';
  static const answerEnd = 'მიხედვით, ეს ურთიერთობა კერძოსამართლებრივია.';

  static final packageInfo = PackageInfo(
    appName: 'fuzzzy_law',
    packageName: 'ge.fuzzycore.fuzzzylaw',
    version: '0.0.0',
    buildNumber: '0',
  );

  static const models = <String, dynamic>{
    'strong': {'model': 'gemini-3.1-pro', 'source': 'env'},
    'cheap': {'model': 'gemini-3.1-flash', 'source': 'env'},
    'available': <Object>[],
    'can_edit': false,
  };

  static const codes = <String, dynamic>{
    'codes': [
      {
        'code_id': codeId,
        'name': codeName,
        'article_count': 1,
        'source_url': 'https://matsne.gov.ge/ka/document/view/31702',
      },
    ],
  };

  static const _chunk = <String, dynamic>{
    'chunk_id': '$articleId.chunk_0',
    'content':
        '$codeName | (#1) | თავი I | მუხლი 1 | $articleTitle\n\n$articleBody',
    'metadata': {
      'code_name': codeName,
      'article_number': 'მუხლი 1',
      'article_title': articleTitle,
    },
  };

  static const codeStructure = <String, dynamic>{
    'chunks': [_chunk],
  };

  static const article = <String, dynamic>{
    'article_id': articleId,
    'chunks': [_chunk],
    'total': 1,
  };
}
