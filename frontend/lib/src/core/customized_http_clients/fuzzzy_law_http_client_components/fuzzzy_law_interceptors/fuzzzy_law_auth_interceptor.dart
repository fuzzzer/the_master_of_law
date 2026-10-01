import 'package:dio/dio.dart';
import 'package:fuzzzy_law/src/src.dart';

class FuzzzyLawAuthInterceptor implements Interceptor {
  FuzzzyLawAuthInterceptor();

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

    // Sent on every request, key or not: without accounts this is the only
    // thing telling the server which install's cases to return. A request
    // that omits it gets bucketed by IP address, so two users on the same
    // network would see each other's legal matters.
    options.headers['X-Device-Id'] = await sl.get<DeviceIdService>().get();

    // The user's own model choice, when they have made one. Sent per request
    // rather than stored server-side: they pay for it with their own key, so
    // switching model must not change anything for anyone else.
    final models = sl.get<ModelPreferenceService>();
    final strong = models.strong;
    final cheap = models.cheap;
    if (strong != null) options.headers['X-Model-Strong'] = strong;
    if (cheap != null) options.headers['X-Model-Cheap'] = cheap;

    handler.next(options);
  }

  @override
  Future<void> onError(DioException err, ErrorInterceptorHandler handler) async {
    // 401 = the stored API key is expired/invalid/revoked. Clear it and signal
    // the app shell to route back to the key prompt instead of leaving the user
    // stuck on a dead "session expired" message.
    if (err.response?.statusCode == 401) {
      try {
        final secureStorage = sl.get<SecureStorageService>();
        await secureStorage.deleteData('temporary_api_key');
      } catch (_) {
        // Best-effort: still emit the event so the redirect fires.
      }
      dataUpdatesHub.sendNotification(const UnauthorizedEvent());
    }
    handler.next(err);
  }

  @override
  void onResponse(
    Response<dynamic> response,
    ResponseInterceptorHandler handler,
  ) {
    handler.next(response);
  }

  /// Carries the user's own Google AI Studio key when the backend runs in
  /// bring-your-own-key mode, and the legacy staging access key otherwise.
  /// The header is the same either way — only the server's reading of it
  /// changes — which is why switching modes needs no client release.
  void _addAuthorization(RequestOptions options, String token) {
    options.headers['X-API-Key'] = token;
  }
}
