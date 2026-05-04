const onlyNumbersRegexMatcher = r'^[0-9]+$';
const onlyLettersRegexMatcher = r'^[A-Za-z]+$';
const onlyLettersAndNumbersRegexMatcher = r'^[A-Za-z0-9]+$';
const emailRegexMatcher = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$';
const onlyPrintableASCIICharactersRegexMatcher = r'^[ -~]+$';

class TextMatchers {
  static bool doesTextContainLargeAndSmallLetters(String text) {
    return RegExp('[A-Z]').hasMatch(text) && RegExp('[a-z]').hasMatch(text);
  }

  static bool doesTextContainNumbers(String text) {
    return RegExp(r'\d').hasMatch(text);
  }

  static bool doesTextContainOnlyPrintableASCIICharacters(String text) {
    return RegExp(r'\d').hasMatch(text);
  }
}
