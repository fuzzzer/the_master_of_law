import 'package:flutter_dotenv/flutter_dotenv.dart';

class ThemasteroflawApiNetworkConfiguration {
  static final themasteroflawBaseUri = dotenv.env['BASE_URI']!;

  const ThemasteroflawApiNetworkConfiguration._();
}
