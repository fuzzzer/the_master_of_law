import 'package:dio/dio.dart';
import 'package:themasteroflaw/src/src.dart';

class ThemasteroflawAuthInterceptor implements Interceptor {
  ThemasteroflawAuthInterceptor();

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
  void onError(DioException err, ErrorInterceptorHandler handler) {
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
