class AppVersionUtils {
  static int compareVersionStrings(String a, String b) {
    if (!isValidVersion(a) || !isValidVersion(b)) {
      throw const FormatException(
        'Version must be of form x.y.z (numbers only).',
      );
    }

    final segmentsOfA = parseVersion(a);
    final segmentsOfB = parseVersion(b);

    for (var i = 0; i < 3; i++) {
      if (segmentsOfA[i] != segmentsOfB[i]) return segmentsOfA[i] < segmentsOfB[i] ? -1 : 1;
    }
    return 0;
  }

  ///Works with versions formatted as "x.y.z"
  static bool isValidVersion(String version) {
    final parts = version.split('.');
    if (parts.length != 3) return false;
    return parts.every((part) => int.tryParse(part) != null);
  }

  static List<int> parseVersion(String version) => version.split('.').map(int.parse).toList();
}
