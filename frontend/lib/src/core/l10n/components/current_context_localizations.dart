import 'package:themasteroflaw/src/src.dart';

ThemasteroflawLocalizations get currentContextLocalizations {
  if (navigatorKey.currentContext == null) {
    return ThemasteroflawLocalizationsKa();
  }

  return ThemasteroflawLocalizations.of(navigatorKey.currentContext!)!;
}
