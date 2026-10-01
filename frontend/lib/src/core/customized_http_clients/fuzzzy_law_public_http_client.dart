import 'package:fuzzzy_law/src/src.dart';

//Exaclty same client as fuzzzyLawHttpClient, just without authentication interceptor
//Used only for authentication api service to avoid infinite request loops
class FuzzzyLawPublicHttpClient extends FuzzzyLawHttpClient {
  FuzzzyLawPublicHttpClient({
    required super.packageInfo,
  }) : super(hasAuthInterceptor: false);
}
