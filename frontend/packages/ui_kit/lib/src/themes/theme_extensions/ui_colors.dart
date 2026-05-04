import 'package:flutter/material.dart';

import '../../colors/colors.dart';

/// Theme extension for accessing app colors via `context.uiColors`.
/// Includes legal-specific colors: trust levels, domain colors, semantic colors.
class UiColors extends ThemeExtension<UiColors> {
  // Core
  final Color primaryColor;
  final Color focusColor;
  final Color secondaryColor;
  final Color errorColor;
  final Color backgroundPrimaryColor;
  final Color backgroundSecondaryColor;
  final Color primaryTextColor;
  final Color secondaryTextColor;

  // Extended semantic
  final Color accentColor;
  final Color successColor;
  final Color warningColor;
  final Color infoColor;
  final Color surfaceColor;

  // Trust levels (for AI messages)
  final Color verifiedColor;
  final Color interpretationColor;
  final Color guidanceColor;

  // Legal domain colors
  final Color criminalColor;
  final Color civilColor;
  final Color administrativeColor;
  final Color laborColor;
  final Color taxColor;
  final Color familyColor;
  final Color propertyColor;
  final Color otherDomainColor;

  const UiColors({
    this.primaryColor = UiKitColors.primaryColor,
    this.focusColor = UiKitColors.focusColor,
    this.secondaryColor = UiKitColors.secondaryColor,
    this.errorColor = UiKitColors.errorColor,
    this.backgroundPrimaryColor = UiKitColors.backgroundPrimaryColor,
    this.backgroundSecondaryColor = UiKitColors.backgroundSecondaryColor,
    this.primaryTextColor = UiKitColors.primaryTextColor,
    this.secondaryTextColor = UiKitColors.secondaryTextColor,
    this.accentColor = UiKitColors.accentColor,
    this.successColor = UiKitColors.successColor,
    this.warningColor = UiKitColors.warningColor,
    this.infoColor = UiKitColors.infoColor,
    this.surfaceColor = UiKitColors.surfaceColor,
    this.verifiedColor = UiKitColors.verifiedColor,
    this.interpretationColor = UiKitColors.interpretationColor,
    this.guidanceColor = UiKitColors.guidanceColor,
    this.criminalColor = UiKitColors.criminalColor,
    this.civilColor = UiKitColors.civilColor,
    this.administrativeColor = UiKitColors.administrativeColor,
    this.laborColor = UiKitColors.laborColor,
    this.taxColor = UiKitColors.taxColor,
    this.familyColor = UiKitColors.familyColor,
    this.propertyColor = UiKitColors.propertyColor,
    this.otherDomainColor = UiKitColors.otherDomainColor,
  });

  const UiColors.light() : this();

  const UiColors.dark()
      : this(
          primaryColor: UiKitColors.primaryColorDark,
          focusColor: UiKitColors.focusColorDark,
          secondaryColor: UiKitColors.secondaryColorDark,
          errorColor: UiKitColors.errorColorDark,
          backgroundPrimaryColor: UiKitColors.backgroundPrimaryColorDark,
          backgroundSecondaryColor: UiKitColors.backgroundSecondaryColorDark,
          primaryTextColor: UiKitColors.primaryTextColorDark,
          secondaryTextColor: UiKitColors.secondaryTextColorDark,
          accentColor: UiKitColors.accentColorDark,
          successColor: UiKitColors.successColorDark,
          warningColor: UiKitColors.warningColorDark,
          infoColor: UiKitColors.infoColorDark,
          surfaceColor: UiKitColors.surfaceColorDark,
          verifiedColor: UiKitColors.verifiedColorDark,
          interpretationColor: UiKitColors.interpretationColorDark,
          guidanceColor: UiKitColors.guidanceColorDark,
          criminalColor: UiKitColors.criminalColorDark,
          civilColor: UiKitColors.civilColorDark,
          administrativeColor: UiKitColors.administrativeColorDark,
          laborColor: UiKitColors.laborColorDark,
          taxColor: UiKitColors.taxColorDark,
          familyColor: UiKitColors.familyColorDark,
          propertyColor: UiKitColors.propertyColorDark,
          otherDomainColor: UiKitColors.otherDomainColorDark,
        );

  @override
  ThemeExtension<UiColors> lerp(ThemeExtension<UiColors>? other, double t) {
    if (other is! UiColors) return this;

    return UiColors(
      primaryColor: Color.lerp(primaryColor, other.primaryColor, t)!,
      focusColor: Color.lerp(focusColor, other.focusColor, t)!,
      secondaryColor: Color.lerp(secondaryColor, other.secondaryColor, t)!,
      errorColor: Color.lerp(errorColor, other.errorColor, t)!,
      backgroundPrimaryColor: Color.lerp(backgroundPrimaryColor, other.backgroundPrimaryColor, t)!,
      backgroundSecondaryColor: Color.lerp(backgroundSecondaryColor, other.backgroundSecondaryColor, t)!,
      primaryTextColor: Color.lerp(primaryTextColor, other.primaryTextColor, t)!,
      secondaryTextColor: Color.lerp(secondaryTextColor, other.secondaryTextColor, t)!,
      accentColor: Color.lerp(accentColor, other.accentColor, t)!,
      successColor: Color.lerp(successColor, other.successColor, t)!,
      warningColor: Color.lerp(warningColor, other.warningColor, t)!,
      infoColor: Color.lerp(infoColor, other.infoColor, t)!,
      surfaceColor: Color.lerp(surfaceColor, other.surfaceColor, t)!,
      verifiedColor: Color.lerp(verifiedColor, other.verifiedColor, t)!,
      interpretationColor: Color.lerp(interpretationColor, other.interpretationColor, t)!,
      guidanceColor: Color.lerp(guidanceColor, other.guidanceColor, t)!,
      criminalColor: Color.lerp(criminalColor, other.criminalColor, t)!,
      civilColor: Color.lerp(civilColor, other.civilColor, t)!,
      administrativeColor: Color.lerp(administrativeColor, other.administrativeColor, t)!,
      laborColor: Color.lerp(laborColor, other.laborColor, t)!,
      taxColor: Color.lerp(taxColor, other.taxColor, t)!,
      familyColor: Color.lerp(familyColor, other.familyColor, t)!,
      propertyColor: Color.lerp(propertyColor, other.propertyColor, t)!,
      otherDomainColor: Color.lerp(otherDomainColor, other.otherDomainColor, t)!,
    );
  }

  @override
  UiColors copyWith({
    Color? primaryColor,
    Color? focusColor,
    Color? secondaryColor,
    Color? errorColor,
    Color? backgroundPrimaryColor,
    Color? backgroundSecondaryColor,
    Color? primaryTextColor,
    Color? secondaryTextColor,
    Color? accentColor,
    Color? successColor,
    Color? warningColor,
    Color? infoColor,
    Color? surfaceColor,
    Color? verifiedColor,
    Color? interpretationColor,
    Color? guidanceColor,
    Color? criminalColor,
    Color? civilColor,
    Color? administrativeColor,
    Color? laborColor,
    Color? taxColor,
    Color? familyColor,
    Color? propertyColor,
    Color? otherDomainColor,
  }) {
    return UiColors(
      primaryColor: primaryColor ?? this.primaryColor,
      focusColor: focusColor ?? this.focusColor,
      secondaryColor: secondaryColor ?? this.secondaryColor,
      errorColor: errorColor ?? this.errorColor,
      backgroundPrimaryColor: backgroundPrimaryColor ?? this.backgroundPrimaryColor,
      backgroundSecondaryColor: backgroundSecondaryColor ?? this.backgroundSecondaryColor,
      primaryTextColor: primaryTextColor ?? this.primaryTextColor,
      secondaryTextColor: secondaryTextColor ?? this.secondaryTextColor,
      accentColor: accentColor ?? this.accentColor,
      successColor: successColor ?? this.successColor,
      warningColor: warningColor ?? this.warningColor,
      infoColor: infoColor ?? this.infoColor,
      surfaceColor: surfaceColor ?? this.surfaceColor,
      verifiedColor: verifiedColor ?? this.verifiedColor,
      interpretationColor: interpretationColor ?? this.interpretationColor,
      guidanceColor: guidanceColor ?? this.guidanceColor,
      criminalColor: criminalColor ?? this.criminalColor,
      civilColor: civilColor ?? this.civilColor,
      administrativeColor: administrativeColor ?? this.administrativeColor,
      laborColor: laborColor ?? this.laborColor,
      taxColor: taxColor ?? this.taxColor,
      familyColor: familyColor ?? this.familyColor,
      propertyColor: propertyColor ?? this.propertyColor,
      otherDomainColor: otherDomainColor ?? this.otherDomainColor,
    );
  }
}
