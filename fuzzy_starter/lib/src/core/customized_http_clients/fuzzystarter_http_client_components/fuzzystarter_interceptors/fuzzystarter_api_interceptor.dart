import 'dart:io';

import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:fuzzystarter/src/src.dart';
import 'package:package_info_plus/package_info_plus.dart';

class FuzzystarterApiInterceptor implements Interceptor {
  final PackageInfo packageInfo;

  FuzzystarterApiInterceptor({required this.packageInfo});

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    logger.d(options.data);

    final headers = options.headers;

    headers['HostVersion'] = packageInfo.version;
    headers['HostBuildNumber'] = packageInfo.buildNumber;
    headers['Platform'] = Platform.operatingSystem;
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
