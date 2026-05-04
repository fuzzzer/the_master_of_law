import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:themasteroflaw/src/src.dart';

class LoggingInterceptor extends Interceptor {
  @override
  void onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) {
    if (appEnvironment.isDevelopment) {
      final curl = _buildCurlCommand(
        requestOptions: options,
      );

      final log =
          '\n'
          'REQUEST: ----------------${options.uri}---------------- \n'
          '\t\tcURL: $curl\n'
          'END OF: ----------------${options.uri}---------------- \n'
          '\n';

      logger.i(log);
      AppLogger.logManager.saveLog(log);
    }

    try {
      final log =
          '\n'
          '\tREQUEST: ${options.method.toUpperCase()} -> ${options.uri}\n'
          '\t\tHEADERS: ${options.headers}\n'
          '\t\tBODY: ${encodeDataBasedOnContentType(data: options.data, headers: options.headers)}'
          '\n';

      logger.i(log);
      AppLogger.logManager.saveLog(log);
    } catch (ex) {
      logger.i('ERROR: Could Not log REQUEST $ex');
    }

    handler.next(options);
  }

  @override
  void onResponse(
    Response<dynamic> response,
    ResponseInterceptorHandler handler,
  ) {
    try {
      final log =
          '\n'
          '\tRESPONSE: ${response.requestOptions.method} -> ${response.requestOptions.uri}\n'
          'StatusCode: ${response.statusCode}'
          '\t\tHEADERS: ${response.headers}\n'
          '\t\tBODY: ${encodeDataBasedOnContentType(data: response.data, headers: response.headers.map)}'
          '\n';

      logger.i(log);

      AppLogger.logManager.saveLog(log);
    } catch (ex) {
      logger.i('ERROR: Could Not log RESPONSE $ex');
    }

    handler.next(response);
  }

  @override
  void onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) {
    try {
      final log =
          '\n'
          '\tRESPONSE ERROR: ${err.requestOptions.method} -> ${err.requestOptions.uri}\n'
          'StatusCode: ${err.response?.statusCode}'
          '\t\tHEADERS: ${err.response?.headers}\n'
          '\t\tBODY: ${encodeDataBasedOnContentType(data: err.response?.data, headers: err.response?.headers.map)}'
          '\t\tError: ${err.error}'
          '\t\tMessage: ${err.message}'
          '\n';

      logger.i(log);
      AppLogger.logManager.saveLog(log);
    } catch (ex) {
      logger.i('ERROR: Could Not log RESPONSE ERROR $ex');
    }

    handler.next(err);
  }

  dynamic encodeDataBasedOnContentType({
    required dynamic data,
    required Map<String, dynamic>? headers,
  }) {
    final dynamic contentType = headers?['Content-Type'] ?? headers?['content-type'];

    String contentTypeValue = '';

    if (contentType is List) {
      final first = contentType.firstOrNull;
      contentTypeValue = first is String ? first : '';
    } else if (contentType is String) {
      contentTypeValue = contentType;
    }

    if (contentTypeValue.toLowerCase().contains('application/json') == true) {
      return jsonEncode(data);
    }

    return data;
  }

  String _buildCurlCommand({
    required RequestOptions requestOptions,
  }) {
    final method = requestOptions.method.toUpperCase();
    final uri = requestOptions.uri.toString();
    final headers = requestOptions.headers;
    final body = requestOptions.data;

    final curlCommand = StringBuffer();

    curlCommand.write('curl -X $method');

    headers.forEach((key, value) {
      curlCommand.write(" -H '$key: $value'");
    });

    if (body != null) {
      final contentType = headers['Content-Type'];

      if (contentType == 'application/json') {
        final encodedBody = _encodeJsonBody(requestOptions);
        curlCommand.write(" -d '$encodedBody'");
      } else if (contentType == 'application/x-www-form-urlencoded') {
        final encodedBody = _encodeFormData(requestOptions);
        curlCommand.write(" -d '$encodedBody'");
      }
    }

    curlCommand.write(" '$uri'");

    return curlCommand.toString();
  }

  String _encodeJsonBody(RequestOptions requestOptions) {
    final jsonBody = requestOptions.data is String ? requestOptions.data : jsonEncode(requestOptions.data);

    return jsonBody as String;
  }

  String _encodeFormData(RequestOptions requestOptions) {
    final formData = FormData.fromMap(requestOptions.data as Map<String, dynamic>);

    final encodedData = <String>[];
    for (final field in formData.fields) {
      final encodedValue = Uri.encodeQueryComponent(field.value);
      encodedData.add('${Uri.encodeQueryComponent(field.key)}=$encodedValue');
    }

    return encodedData.join('&');
  }
}
