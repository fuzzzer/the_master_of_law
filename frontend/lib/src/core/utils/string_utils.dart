class StringUtils {
  static bool isValidUrl(String? urlString) {
    if (urlString == null || urlString.isEmpty) {
      return false;
    }
    final Uri? uri = Uri.tryParse(urlString);
    return uri != null && (uri.isScheme('http') || uri.isScheme('https'));
  }

  static String getLastCharacters(
    String input, {
    int count = 4,
  }) {
    return input.length >= count ? input.substring(input.length - count) : input;
  }
}
