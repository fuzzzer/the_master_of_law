import 'package:flutter/material.dart';
import 'package:ui_kit/ui_kit.dart';

export 'components/components.dart';
export 'components/exports.dart';

class CountryPicker extends StatefulWidget {
  const CountryPicker({
    super.key,
    required this.onChanged,
  });

  final void Function(DropdownItem?) onChanged;

  @override
  State<CountryPicker> createState() => _CountryPickerState();
}

class _CountryPickerState extends State<CountryPicker> {
  late List<Country> countries;
  late Country selectedCountry;
  late List<DropdownItem> dropdownItems;

  @override
  void initState() {
    super.initState();

    dropdownItems = getDropdownItems();
  }

  List<DropdownItem> getDropdownItems() {
    countries = countryCodes.map((country) => Country.from(json: country)).toList();

    selectedCountry = countries.firstWhere((country) => country.phoneCode == '995');

    return countries.map((country) {
      final label = getCountryDisplay(country);
      return DropdownItem(label: label, valueId: label);
    }).toList();
  }

  String getCountryDisplay(Country country) {
    return "${country.flagEmoji} +${country.phoneCode}";
  }

  @override
  Widget build(BuildContext context) {
    // final theme = Theme.of(context);
    // final uiColors = theme.extension<UiColors>()!;

    final label = getCountryDisplay(selectedCountry);

    return PrimaryDropdown(
      items: dropdownItems,
      onChanged: widget.onChanged,
      selectedItem: DropdownItem(label: label, valueId: label),
      borderColor: Colors.transparent,
      stepWidth: 0,
    );
  }
}
