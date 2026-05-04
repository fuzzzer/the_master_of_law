import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

import 'themes.dart';

/// The Master of Law — Theme Configuration
/// Dark mode is DEFAULT. Deep navy backgrounds with warm gold accents.
class UiKitTheme {
  static const UiColors lightUiColors = UiColors.light();
  static const UiColors darkUiColors = UiColors.dark();

  static final UiTextStyles uiTextStyles = UiTextStyles();

  static ColorScheme lightColorScheme() => ColorScheme.light(
        primary: lightUiColors.accentColor,
        onPrimary: lightUiColors.backgroundPrimaryColor,
        secondary: lightUiColors.secondaryColor,
        onSecondary: lightUiColors.primaryTextColor,
        error: lightUiColors.errorColor,
        onError: lightUiColors.backgroundPrimaryColor,
        surface: lightUiColors.backgroundSecondaryColor,
        onSurface: lightUiColors.primaryTextColor,
      );

  static ColorScheme darkColorScheme() => ColorScheme.dark(
        primary: darkUiColors.accentColor,
        onPrimary: darkUiColors.backgroundPrimaryColor,
        secondary: darkUiColors.secondaryColor,
        onSecondary: darkUiColors.primaryTextColor,
        error: darkUiColors.errorColor,
        onError: darkUiColors.backgroundPrimaryColor,
        surface: darkUiColors.backgroundSecondaryColor,
        onSurface: darkUiColors.primaryTextColor,
      );

  static ThemeData light({
    Locale locale = const Locale('en'),
    UiFormStyles uiFormStyles = const UiFormStyles.original(),
  }) {
    return ThemeData(
      brightness: Brightness.light,
      useMaterial3: true,
      scaffoldBackgroundColor: lightUiColors.backgroundPrimaryColor,
      colorScheme: lightColorScheme(),
      textTheme: GoogleFonts.notoSansGeorgianTextTheme(
        ThemeData.light(useMaterial3: true).textTheme,
      ).apply(
        bodyColor: lightUiColors.primaryTextColor,
        displayColor: lightUiColors.primaryTextColor,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: lightUiColors.backgroundPrimaryColor,
        foregroundColor: lightUiColors.primaryTextColor,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: lightUiColors.backgroundSecondaryColor,
        selectedItemColor: lightUiColors.accentColor,
        unselectedItemColor: lightUiColors.secondaryTextColor,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
        selectedLabelStyle: GoogleFonts.notoSansGeorgian(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          height: 1.5,
        ),
        unselectedLabelStyle: GoogleFonts.notoSansGeorgian(
          fontSize: 12,
          fontWeight: FontWeight.w400,
          height: 1.5,
        ),
      ),
      cardTheme: CardThemeData(
        color: lightUiColors.backgroundSecondaryColor,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(
            color: lightUiColors.secondaryColor.withValues(alpha: 0.15),
          ),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: lightUiColors.secondaryColor.withValues(alpha: 0.15),
        thickness: 1,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: lightUiColors.surfaceColor,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: lightUiColors.surfaceColor,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
      extensions: <ThemeExtension<dynamic>>[
        lightUiColors,
        uiTextStyles.apply(color: lightUiColors.primaryTextColor),
        uiFormStyles,
      ],
    );
  }

  static ThemeData dark({
    Locale locale = const Locale('en'),
    UiFormStyles uiFormStyles = const UiFormStyles.original(),
  }) {
    return ThemeData(
      brightness: Brightness.dark,
      useMaterial3: true,
      scaffoldBackgroundColor: darkUiColors.backgroundPrimaryColor,
      colorScheme: darkColorScheme(),
      textTheme: GoogleFonts.notoSansGeorgianTextTheme(
        ThemeData.dark(useMaterial3: true).textTheme,
      ).apply(
        bodyColor: darkUiColors.primaryTextColor,
        displayColor: darkUiColors.primaryTextColor,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: darkUiColors.backgroundPrimaryColor,
        foregroundColor: darkUiColors.primaryTextColor,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
      ),
      bottomNavigationBarTheme: BottomNavigationBarThemeData(
        backgroundColor: darkUiColors.backgroundSecondaryColor,
        selectedItemColor: darkUiColors.accentColor,
        unselectedItemColor: darkUiColors.secondaryTextColor,
        type: BottomNavigationBarType.fixed,
        elevation: 0,
        selectedLabelStyle: GoogleFonts.notoSansGeorgian(
          fontSize: 12,
          fontWeight: FontWeight.w600,
          height: 1.5,
        ),
        unselectedLabelStyle: GoogleFonts.notoSansGeorgian(
          fontSize: 12,
          fontWeight: FontWeight.w400,
          height: 1.5,
        ),
      ),
      cardTheme: CardThemeData(
        color: darkUiColors.backgroundSecondaryColor,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
          side: BorderSide(
            color: darkUiColors.secondaryColor.withValues(alpha: 0.12),
          ),
        ),
      ),
      dividerTheme: DividerThemeData(
        color: darkUiColors.secondaryColor.withValues(alpha: 0.12),
        thickness: 1,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: darkUiColors.surfaceColor,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      ),
      chipTheme: ChipThemeData(
        backgroundColor: darkUiColors.surfaceColor,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
      extensions: <ThemeExtension<dynamic>>[
        darkUiColors,
        uiTextStyles.apply(color: darkUiColors.primaryTextColor),
        uiFormStyles,
      ],
    );
  }
}
