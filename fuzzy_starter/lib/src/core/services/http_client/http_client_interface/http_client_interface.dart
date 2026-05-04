import 'package:dio/dio.dart';

export 'http_client_exceptions/http_client_exceptions.dart';

abstract class HttpClientInterface {
  Future<Response<T>> get<T>(
    Uri uri, {
    Options? options,
    CancelToken? cancelToken,
    void Function(int, int)? onReceiveProgress,
  });

  Future<Response<T>> post<T>(
    Uri uri, {
    Object? body,
    Options? options,
    CancelToken? cancelToken,
    void Function(int, int)? onSendProgress,
    void Function(int, int)? onReceiveProgress,
  });

  Future<Response<T>> put<T>(
    Uri uri, {
    Object? body,
    Options? options,
    CancelToken? cancelToken,
    void Function(int, int)? onSendProgress,
    void Function(int, int)? onReceiveProgress,
  });

  Future<Response<T>> patch<T>(
    Uri uri, {
    Object? body,
    Options? options,
    CancelToken? cancelToken,
    void Function(int, int)? onSendProgress,
    void Function(int, int)? onReceiveProgress,
  });

  Future<Response<T>> delete<T>(
    Uri uri, {
    Object? body,
    Options? options,
    CancelToken? cancelToken,
  });
}
