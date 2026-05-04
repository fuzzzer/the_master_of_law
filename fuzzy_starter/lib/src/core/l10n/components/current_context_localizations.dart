import 'package:fuzzystarter/src/src.dart';

FuzzystarterLocalizations get currentContextLocalizations {
  if (navigatorKey.currentContext == null) {
    return FuzzystarterLocalizationsEn();
  }

  return FuzzystarterLocalizations.of(navigatorKey.currentContext!)!;
}
