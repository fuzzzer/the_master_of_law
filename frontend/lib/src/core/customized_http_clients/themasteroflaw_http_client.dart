import 'package:dio/dio.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:themasteroflaw/src/src.dart';

export 'themasteroflaw_http_client_components/themasteroflaw_http_client_components.dart';
export 'themasteroflaw_public_http_client.dart';

class ThemasteroflawHttpClient extends HttpClientInterface {
  final Dio _dio;

  ThemasteroflawHttpClient({
    required PackageInfo packageInfo,
    bool hasApiInterceptor = true,
    bool hasAuthInterceptor = true,
    bool hasLoggingInterceptor = true,
  }) : _dio = Dio(DefaultBaseOptions()) {
    _dio.interceptors.addAll([
      if (hasApiInterceptor) ThemasteroflawApiInterceptor(packageInfo: packageInfo),
      if (hasAuthInterceptor) ThemasteroflawAuthInterceptor(),
      if (hasLoggingInterceptor) LoggingInterceptor(),
    ]);
  }

  @override
  Future<Response<T>> get<T>(
    Uri uri, {
    Options? options,
    CancelToken? cancelToken,
    void Function(int, int)? onReceiveProgress,
    bool throwExceptionOnthemasteroflawUnsuccessfulResponse = true,
  }) async {
    try {
      return await _dio.getUri<T>(
        uri,
        options: options,
        onReceiveProgress: onReceiveProgress,
      );
    } on DioException catch (ex) {
      logger.e(ex);
      throw ThemasteroflawRestApiExceptionTranslator.translateToHttpClientException(
        ex,
      );
    } catch (ex, stackTrace) {
      logger.e(ex, stackTrace: stackTrace);

      rethrow;
    }
  }

  @override
  Future<Response<T>> post<T>(
    Uri uri, {
    Object? body,
    Map<String, String>? headers,
    Options? options,
    CancelToken? cancelToken,
    void Function(int, int)? onSendProgress,
    void Function(int, int)? onReceiveProgress,
    bool handlesthemasteroflawErrors = true,
  }) async {
    try {
      return await _dio.postUri<T>(
        uri,
        data: body,
        options: options,
        cancelToken: cancelToken,
        onSendProgress: onSendProgress,
        onReceiveProgress: onReceiveProgress,
      );
    } on DioException catch (ex) {
      logger.e(ex);
      throw ThemasteroflawRestApiExceptionTranslator.translateToHttpClientException(ex);
    } catch (ex, stackTrace) {
      logger.e(ex, stackTrace: stackTrace);

      rethrow;
    }
  }

  @override
  Future<Response<T>> put<T>(
    Uri uri, {
    Object? body,
    Map<String, String>? headers,
    Options? options,
    CancelToken? cancelToken,
    void Function(int, int)? onSendProgress,
    void Function(int, int)? onReceiveProgress,
  }) async {
    try {
      return await _dio.putUri<T>(
        uri,
        data: body,
        options: options,
        cancelToken: cancelToken,
        onSendProgress: onSendProgress,
        onReceiveProgress: onReceiveProgress,
      );
    } on DioException catch (ex) {
      logger.e(ex);
      throw ThemasteroflawRestApiExceptionTranslator.translateToHttpClientException(
        ex,
      );
    } catch (ex, stackTrace) {
      logger.e(ex, stackTrace: stackTrace);

      rethrow;
    }
  }

  @override
  Future<Response<T>> patch<T>(
    Uri uri, {
    Object? body,
    Options? options,
    CancelToken? cancelToken,
    void Function(int, int)? onSendProgress,
    void Function(int, int)? onReceiveProgress,
  }) async {
    try {
      return await _dio.patchUri<T>(
        uri,
        data: body,
        options: options,
        cancelToken: cancelToken,
        onSendProgress: onSendProgress,
        onReceiveProgress: onReceiveProgress,
      );
    } on DioException catch (ex) {
      logger.e(ex);
      throw ThemasteroflawRestApiExceptionTranslator.translateToHttpClientException(
        ex,
      );
    } catch (ex, stackTrace) {
      logger.e(ex, stackTrace: stackTrace);

      rethrow;
    }
  }

  @override
  Future<Response<T>> delete<T>(
    Uri uri, {
    Object? body,
    Options? options,
    CancelToken? cancelToken,
  }) async {
    try {
      return await _dio.deleteUri<T>(
        uri,
        data: body,
        options: options,
        cancelToken: cancelToken,
      );
    } on DioException catch (ex) {
      logger.e(ex);
      throw ThemasteroflawRestApiExceptionTranslator.translateToHttpClientException(
        ex,
      );
    } catch (ex, stackTrace) {
      logger.e(ex, stackTrace: stackTrace);

      rethrow;
    }
  }
}
