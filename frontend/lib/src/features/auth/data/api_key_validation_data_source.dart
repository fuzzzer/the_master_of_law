import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:fuzzzy_law/src/src.dart';

/// Outcome of checking a pasted key against Google, via our backend.
enum ApiKeyCheck {
  /// Google accepted it — the key can actually run the app.
  valid,

  /// Google rejected it: typo, revoked, or the Generative Language API is off.
  invalid,

  /// The backend was unreachable. Says nothing about the key.
  unreachable,
}

/// Verifies a bring-your-own-key credential at the moment the user pastes it.
///
/// WHY THIS EXISTS: the previous check called the credits endpoint and treated
/// "server answered at all" as success, which passes for any string the server
/// happens not to reject. Under BYOK the key is a live Google credential, and
/// a wrong one looks completely fine until the user has typed out their legal
/// problem and is watching a spinner fail. The backend's /validate endpoint
/// asks Google directly and costs no tokens, so the answer is available while
/// the user still has the key on their clipboard.
class ApiKeyValidationDataSource {
  ApiKeyValidationDataSource() : _httpClient = sl.get<FuzzzyLawHttpClient>();

  final FuzzzyLawHttpClient _httpClient;

  Future<ApiKeyCheck> validate() async {
    final base = dotenv.env['API_BASE_URL'] ?? 'http://127.0.0.1:8000';
    try {
      final response = await _httpClient.get<Map<String, dynamic>>(
        Uri.parse('$base/api/v1/api-keys/validate'),
      );
      return response.data?['valid'] == true
          ? ApiKeyCheck.valid
          : ApiKeyCheck.invalid;
    } on DioException catch (e) {
      final status = e.response?.statusCode;
      if (status == 401 || status == 403) return ApiKeyCheck.invalid;
      return ApiKeyCheck.unreachable;
    } catch (_) {
      // The http client translates Dio failures into its own exception type,
      // so an unrecognised error here is a transport problem, not a verdict
      // on the key — saying "your key is wrong" would send the user chasing
      // a good key while the server is simply down.
      return ApiKeyCheck.unreachable;
    }
  }
}
