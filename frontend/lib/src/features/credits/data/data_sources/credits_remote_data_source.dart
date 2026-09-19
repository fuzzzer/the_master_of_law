import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:fuzzzy_law/src/src.dart';

/// Remote data source for the user's credit balance.
class CreditsRemoteDataSource {
  final FuzzzyLawHttpClient _httpClient;

  CreditsRemoteDataSource() : _httpClient = sl.get<FuzzzyLawHttpClient>();

  Uri _uri(String path) => Uri.parse(
        '${dotenv.env['API_BASE_URL'] ?? 'http://127.0.0.1:8000'}$path',
      );

  /// GET /api/v1/account/credits — current credit balance for the API key.
  Future<Map<String, dynamic>> getCredits() async {
    final response = await _httpClient.get<Map<String, dynamic>>(
      _uri('/api/v1/account/credits'),
    );
    return response.data!;
  }
}
