import 'package:dio/dio.dart';

class DefaultBaseOptions extends BaseOptions {
  DefaultBaseOptions()
    : super(
        // Sane global timeouts: a dead/unreachable server must not leave the UI
        // spinning for minutes. Long-running AI endpoints (chat / case build)
        // override receiveTimeout per-request via [longRunningRequest].
        connectTimeout: const Duration(seconds: 15),
        receiveTimeout: const Duration(seconds: 30),
        sendTimeout: const Duration(seconds: 30),
        responseType: ResponseType.json,
        contentType: 'application/json',
      );
}

/// Generous receive timeout for legitimately long AI endpoints (case build,
/// agent turns) that can take 30-60s. Use as the `options:` on those calls.
Options longRunningRequest() =>
    Options(receiveTimeout: const Duration(seconds: 120));
