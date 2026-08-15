import 'package:dio/dio.dart';
import 'package:fuzzzy_law/src/src.dart';

class FuzzzyLawAuthInterceptor implements Interceptor {
  FuzzzyLawAuthInterceptor();

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final secureStorage = sl.get<SecureStorageService>();
    final apiKey = await secureStorage.getData('temporary_api_key');
    
    if (apiKey != null && apiKey.isNotEmpty) {
      _addAuthorization(options, apiKey);
    }

    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    // 401 = the stored API key is expired/invalid/revoked. Clear it and signal
    // the app shell to route back to the key prompt instead of leaving the user
    // stuck on a dead "session expired" message.
    if (err.response?.statusCode == 401) {
      try {
        final secureStorage = sl.get<SecureStorageService>();
        await secureStorage.deleteData('temporary_api_key');
      } catch (_) {
        // Best-effort: still emit the event so the redirect fires.
      }
      dataUpdatesHub.sendNotification(const UnauthorizedEvent());
    }
    handler.next(err);
  }

  @override
  void onResponse(
    Response<dynamic> response,
    ResponseInterceptorHandler handler,
  ) {
    handler.next(response);
  }

  void _addAuthorization(RequestOptions options, String token) {
    options.headers['X-API-Key'] = token;
  }
}
