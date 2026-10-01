import 'package:flutter_dotenv/flutter_dotenv.dart';

class FuzzzyLawApiNetworkConfiguration {
  static final fuzzzyLawBaseUri = dotenv.env['BASE_URI']!;

  const FuzzzyLawApiNetworkConfiguration._();
}
