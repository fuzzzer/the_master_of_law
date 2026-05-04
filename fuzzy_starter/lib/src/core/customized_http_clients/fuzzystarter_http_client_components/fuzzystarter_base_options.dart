import 'package:dio/dio.dart';

class DefaultBaseOptions extends BaseOptions {
  DefaultBaseOptions()
      : super(
          receiveTimeout: const Duration(seconds: 20),
          connectTimeout: const Duration(seconds: 20),
          sendTimeout: const Duration(seconds: 20),
          responseType: ResponseType.json,
          contentType: 'application/json',
        );
}
