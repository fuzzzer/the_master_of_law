import 'package:fuzzystarter/src/src.dart';

//Exaclty same client as FuzzystarterHttpClient, just without authentication interceptor
//Used only for authentication api service to avoid infinite request loops
class FuzzystarterPublicHttpClient extends FuzzystarterHttpClient {
  FuzzystarterPublicHttpClient({
    required super.packageInfo,
  }) : super(hasAuthInterceptor: false);
}
