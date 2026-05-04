import 'package:dio/dio.dart';

class FuzzystarterAuthInterceptor implements Interceptor {
  FuzzystarterAuthInterceptor();

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    //TODO add auth token from your desired source
    _addAuthorization(options, 'tochange');

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

  void _addAuthorization(RequestOptions options, String token) {}
}
