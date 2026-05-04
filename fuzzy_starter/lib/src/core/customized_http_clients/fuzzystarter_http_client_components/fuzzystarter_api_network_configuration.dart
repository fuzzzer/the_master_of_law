import 'package:flutter_dotenv/flutter_dotenv.dart';

class FuzzystarterApiNetworkConfiguration {
  static final fuzzystarterBaseUri = dotenv.env['BASE_URI']!;

  const FuzzystarterApiNetworkConfiguration._();
}
