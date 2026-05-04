import 'package:themasteroflaw/src/src.dart';

//Exaclty same client as themasteroflawHttpClient, just without authentication interceptor
//Used only for authentication api service to avoid infinite request loops
class ThemasteroflawPublicHttpClient extends ThemasteroflawHttpClient {
  ThemasteroflawPublicHttpClient({
    required super.packageInfo,
  }) : super(hasAuthInterceptor: false);
}
