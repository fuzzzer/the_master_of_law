import 'package:themasteroflaw/src/src.dart';

class CommonTextValidators {
  static String? validateLatinText({
    required String text,
    required ThemasteroflawLocalizations localizations,
    int minLength = 2,
  }) {
    if (text.length < minLength) {
      return localizations.minimumCharacters(minLength);
    }

    if (!RegExp(onlyLettersAndNumbersRegexMatcher).hasMatch(text)) {
      return localizations.useOnlyLatinLetters;
    }

    return null;
  }

  static String? validateEmail({
    required String email,
    required ThemasteroflawLocalizations localizations,
  }) {
    if (!RegExp(emailRegexMatcher).hasMatch(email)) {
      return localizations.wrongFormat;
    }

    return null;
  }

  static String? validatePassword({
    required String password,
    required ThemasteroflawLocalizations localizations,
  }) {
    if (password.isNotEmpty && !RegExp(onlyPrintableASCIICharactersRegexMatcher).hasMatch(password)) {
      return localizations.useOnlyLatinLetters;
    }

    return null;
  }

  static String? validateOtpCode({
    required String otpCode,
    int otpLength = 6,
    required ThemasteroflawLocalizations localizations,
  }) {
    if (otpCode.isNotEmpty && otpCode.length != otpLength || !RegExp(onlyNumbersRegexMatcher).hasMatch(otpCode)) {
      return localizations.wrongFormat;
    }

    return null;
  }
}
