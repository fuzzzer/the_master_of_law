import 'package:dio/dio.dart';

class DefaultBaseOptions extends BaseOptions {
  DefaultBaseOptions()
    : super(
        receiveTimeout: const Duration(seconds: 520),
        connectTimeout: const Duration(seconds: 520),
        sendTimeout: const Duration(seconds: 520),
        responseType: ResponseType.json,
        contentType: 'application/json',
      );
}
