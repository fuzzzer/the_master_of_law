
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:package_info_plus/package_info_plus.dart';

class FuzzzyLawApiInterceptor implements Interceptor {
  final PackageInfo packageInfo;

  FuzzzyLawApiInterceptor({required this.packageInfo});

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    logger.d(options.data);

    final headers = options.headers;

    headers['HostVersion'] = packageInfo.version;
    headers['HostBuildNumber'] = packageInfo.buildNumber;
    headers['Platform'] = kIsWeb ? 'web' : defaultTargetPlatform.name;
    headers['Debug'] = kDebugMode.toString();

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
}
