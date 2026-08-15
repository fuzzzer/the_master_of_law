import 'package:fuzzzy_law/src/src.dart';

FuzzzyLawLocalizations get currentContextLocalizations {
  if (navigatorKey.currentContext == null) {
    return FuzzzyLawLocalizationsKa();
  }

  return FuzzzyLawLocalizations.of(navigatorKey.currentContext!)!;
}
