import 'package:ui_kit/ui_kit.dart';

class Country {
  final String phoneCode;
  final String countryCode;
  final String name;

  Country({required this.phoneCode, required this.countryCode, required this.name});

  Country.from({required Map<String, dynamic> json})
    : phoneCode = json['e164_cc'],
      countryCode = json['iso2_cc'],
      name = json['name'];

  static Country parse(String country) {
    return Country.from(json: countryCodes.singleWhere((Map<String, dynamic> c) => c['iso2_cc'] == country));
  }

  Map<String, dynamic> toJson() {
    final Map<String, dynamic> data = <String, dynamic>{};
    data['e164_cc'] = phoneCode;
    data['iso2_cc'] = countryCode;
    data['name'] = name;

    return data;
  }

  @override
  bool operator ==(Object other) {
    if (other is Country) {
      return other.countryCode == countryCode;
    }
    return super == other;
  }

  @override
  int get hashCode => countryCode.hashCode;

  String get flagEmoji => countryCodeToEmoji(countryCode);

  static String countryCodeToEmoji(String countryCode) {
    final int firstLetter = countryCode.codeUnitAt(0) - 0x41 + 0x1F1E6;
    final int secondLetter = countryCode.codeUnitAt(1) - 0x41 + 0x1F1E6;
    return String.fromCharCode(firstLetter) + String.fromCharCode(secondLetter);
  }
}
