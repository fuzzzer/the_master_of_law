import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:ui_kit/ui_kit.dart';

/// The Master of Law — the ONE bridge from `fuzzzy_ui_kit` to Flutter's
/// [ThemeData].
///
/// Phase M · Unit A. Replaces the forked `UiKitTheme.dark()/light()`. Three
/// jobs, in order:
///
/// 1. **Roles.** `FuzzzyTheme.build(inkPack, night|paper)` is the kit's single
///    role→ThemeData bridge. Everything below only ever *adds* to what it
///    returns; no role value is ever restated as a literal here.
/// 2. **Georgian glyph coverage.** The Ink pack's families (Space Grotesk /
///    Inter / Space Mono) have **no Georgian block**, and this is a Georgian
///    app. Every kit type role gets a weight-matched Noto Sans Georgian
///    `fontFamilyFallback` so Georgian renders in a typeface *we* control —
///    see [_georgianize]. Interim app-side fix for
///    `design/PHASE_M_KIT_QUEUE.md` item 6; the kit stays read-only.
/// 3. **Material sub-themes, from kit roles.** `FuzzzyTheme.build` sets only
///    `brightness / scaffoldBackgroundColor / canvasColor / colorScheme /
///    dividerColor / textTheme / extensions`. It deliberately sets no
///    `cardTheme`, `inputDecorationTheme`, `appBarTheme`, `chipTheme`,
///    `dividerTheme` or `bottomNavigationBarTheme`, because kit components
///    read roles directly and never Material's sub-themes. The forked theme
///    *did* set all six, and ~80 stock-Material widgets in this app still
///    depend on them. Restating them here from kit roles is what keeps those
///    surfaces correct while the widget swap (M11) is in flight. See
///    [_appBar] … [_bottomNav].
///
/// **Transitional, and deliberately so.** Until M12 deletes `packages/ui_kit`,
/// the fork's own extensions are ALSO attached (see [_legacyExtensions]) so
/// that not-yet-migrated `context.uiColors` / `context.uiTextStyles` reads keep
/// resolving instead of throwing. Both extension families can coexist: Flutter
/// keys `ThemeData.extensions` by runtime type.
abstract final class ThemasteroflawTheme {
  /// Ink · night skin. The app's default (the fork's dark mode).
  static ThemeData dark() => _build(FuzzzySkin.night, UiKitTheme.dark());

  /// Ink · paper skin.
  static ThemeData light() => _build(FuzzzySkin.paper, UiKitTheme.light());

  static ThemeData _build(FuzzzySkin skin, ThemeData legacy) {
    final base = FuzzzyTheme.build(inkPack, skin);

    final colors = base.extension<FuzzzyColors>()!;
    final radius = base.extension<FuzzzyRadius>()!;
    final form = base.extension<FuzzzyFormStyles>()!;
    final type = base.extension<FuzzzyTextStyles>()!.mapStyles(_georgianize);

    return base.copyWith(
      textTheme: _mapTextTheme(base.textTheme, _georgianize),
      appBarTheme: _appBar(colors, type),
      cardTheme: _card(colors, radius),
      dividerTheme: _divider(colors),
      inputDecorationTheme: _input(colors, type, form),
      chipTheme: _chip(colors, radius, type),
      bottomNavigationBarTheme: _bottomNav(colors, type),
      extensions: <ThemeExtension<dynamic>>[
        ...base.extensions.values.where((e) => e is! FuzzzyTextStyles),
        type,
        ..._legacyExtensions(legacy),
      ],
    );
  }

  // ---------------------------------------------------------------------------
  // Georgian fallback (PHASE_M_KIT_QUEUE item 6 — interim, app-side)
  // ---------------------------------------------------------------------------

  /// Cache of `FontWeight` → the GoogleFonts-registered Noto Sans Georgian
  /// family name for that weight (e.g. `NotoSansGeorgian_w600`).
  ///
  /// The call that produces the name is also what *registers* the font with
  /// Flutter's font loader, so this map must be populated through
  /// [GoogleFonts.notoSansGeorgian] and never hand-written.
  static final Map<FontWeight, String> _georgianFamilies = {};

  /// Append a weight-matched Georgian fallback to [base].
  ///
  /// Weight matters: GoogleFonts registers one family per variant, so a single
  /// blanket fallback would render every Georgian string at regular weight
  /// while the Latin next to it stayed bold. Resolving per style keeps the two
  /// scripts on the same weight ramp.
  static TextStyle _georgianize(TextStyle base) {
    final weight = base.fontWeight ?? FontWeight.w400;
    final family = _georgianFamilies.putIfAbsent(
      weight,
      () => GoogleFonts.notoSansGeorgian(fontWeight: weight).fontFamily!,
    );
    return base.copyWith(
      fontFamilyFallback: [family, ...?base.fontFamilyFallback],
    );
  }

  /// Mechanical per-slot map over a [TextTheme]. Deliberately does not restate
  /// the kit's role→Material-slot mapping — it transforms whatever
  /// `FuzzzyTheme.build` already produced.
  static TextTheme _mapTextTheme(
    TextTheme theme,
    TextStyle Function(TextStyle) f,
  ) {
    TextStyle? map(TextStyle? style) => style == null ? null : f(style);
    return TextTheme(
      displayLarge: map(theme.displayLarge),
      displayMedium: map(theme.displayMedium),
      displaySmall: map(theme.displaySmall),
      headlineLarge: map(theme.headlineLarge),
      headlineMedium: map(theme.headlineMedium),
      headlineSmall: map(theme.headlineSmall),
      titleLarge: map(theme.titleLarge),
      titleMedium: map(theme.titleMedium),
      titleSmall: map(theme.titleSmall),
      bodyLarge: map(theme.bodyLarge),
      bodyMedium: map(theme.bodyMedium),
      bodySmall: map(theme.bodySmall),
      labelLarge: map(theme.labelLarge),
      labelMedium: map(theme.labelMedium),
      labelSmall: map(theme.labelSmall),
    );
  }

  // ---------------------------------------------------------------------------
  // Material sub-themes — every value below is a kit ROLE, never a literal.
  // ---------------------------------------------------------------------------

  /// 14 stock `AppBar` sites. Flat on `ground`, ink foreground, no scroll
  /// elevation — the Ink surface has no shadow vocabulary.
  static AppBarTheme _appBar(FuzzzyColors c, FuzzzyTextStyles t) => AppBarTheme(
        backgroundColor: c.ground,
        foregroundColor: c.ink,
        surfaceTintColor: Colors.transparent,
        elevation: 0,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: t.titleL.copyWith(color: c.ink),
        iconTheme: IconThemeData(color: c.ink),
        actionsIconTheme: IconThemeData(color: c.ink),
      );

  /// 28 stock `Card` sites. Material 3's default card is an elevated, tinted,
  /// shadow-casting surface; Ink cards are a flat `surface` panel with a
  /// hairline `line` border.
  static CardThemeData _card(FuzzzyColors c, FuzzzyRadius r) => CardThemeData(
        color: c.surface,
        surfaceTintColor: Colors.transparent,
        shadowColor: Colors.transparent,
        elevation: 0,
        margin: EdgeInsets.zero,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(r.m),
          side: BorderSide(color: c.line),
        ),
      );

  /// 6 stock `Divider` sites. Material 3 resolves a divider's colour from
  /// `colorScheme.outlineVariant` (which the kit binds to `lineStrong`), NOT
  /// from `ThemeData.dividerColor` — so without this, every hairline would be
  /// drawn one step too heavy.
  static DividerThemeData _divider(FuzzzyColors c) => DividerThemeData(
        color: c.line,
        thickness: 1,
        space: 1,
      );

  /// 19 stock `InputDecoration` sites. Mirrors `FuzzzyTextField`'s box exactly
  /// (fill / idleBorder / focusBorder / errorBorder / disabledBorder at
  /// `form.borderWidth`, `form.radius` corners, `form.contentPadding`) so a
  /// Material field and a kit field are indistinguishable during the swap.
  ///
  /// Every border state is declared at the same width on purpose: state
  /// changes must only ever recolour, never reflow.
  static InputDecorationTheme _input(
    FuzzzyColors c,
    FuzzzyTextStyles t,
    FuzzzyFormStyles form,
  ) {
    OutlineInputBorder border(Color color) => OutlineInputBorder(
          borderRadius: BorderRadius.circular(form.radius),
          borderSide: BorderSide(color: color, width: form.borderWidth),
        );

    return InputDecorationTheme(
      filled: true,
      fillColor: c.fill,
      contentPadding: form.contentPadding,
      border: border(c.idleBorder),
      enabledBorder: border(c.idleBorder),
      focusedBorder: border(c.focusBorder),
      errorBorder: border(c.errorBorder),
      focusedErrorBorder: border(c.errorBorder),
      disabledBorder: border(c.disabledBorder),
      hintStyle: t.body.copyWith(color: c.hint),
      labelStyle: t.label.copyWith(color: c.fieldLabel),
      floatingLabelStyle: t.label.copyWith(color: c.focusBorder),
      helperStyle: t.bodyS.copyWith(color: c.helper),
      errorStyle: t.bodyS.copyWith(color: c.errorText),
      prefixStyle: t.body.copyWith(color: c.fieldText),
      suffixStyle: t.body.copyWith(color: c.fieldText),
    );
  }

  /// 13 stock `Chip` sites. Unselected reads as a `surface` pill on a `line`
  /// hairline; selected inverts to `actionPrimary` — the kit's inverted-mono
  /// selection, deliberately NOT red (`harvest/mol.md` §4, red discipline).
  static ChipThemeData _chip(
    FuzzzyColors c,
    FuzzzyRadius r,
    FuzzzyTextStyles t,
  ) =>
      ChipThemeData(
        backgroundColor: c.surface,
        selectedColor: c.actionPrimaryBg,
        disabledColor: c.track,
        surfaceTintColor: Colors.transparent,
        checkmarkColor: c.actionPrimaryFg,
        elevation: 0,
        pressElevation: 0,
        side: BorderSide(color: c.line),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(r.s),
        ),
        labelStyle: t.label.copyWith(color: c.ink),
        secondaryLabelStyle: t.label.copyWith(color: c.actionPrimaryFg),
      );

  /// 1 stock `BottomNavigationBar` site (`main_shell`). Selected item uses
  /// `ink` rather than a brand accent — Ink keeps navigation monochrome.
  static BottomNavigationBarThemeData _bottomNav(
    FuzzzyColors c,
    FuzzzyTextStyles t,
  ) =>
      BottomNavigationBarThemeData(
        backgroundColor: c.surface,
        selectedItemColor: c.ink,
        unselectedItemColor: c.inkMute,
        selectedLabelStyle: t.label.copyWith(color: c.ink),
        unselectedLabelStyle: t.label.copyWith(color: c.inkMute),
        type: BottomNavigationBarType.fixed,
        elevation: 0,
      );

  // ---------------------------------------------------------------------------
  // Transitional bridge — DELETE WITH `packages/ui_kit` AT M12
  // ---------------------------------------------------------------------------

  /// The forked `UiColors` / `UiTextStyles` / `UiFormStyles` extensions, taken
  /// straight off the fork's own [ThemeData] so no fork value is restated here.
  ///
  /// Without this, the instant this file replaces `UiKitTheme`, every
  /// not-yet-migrated `Theme.of(context).extension<UiColors>()!` in the app
  /// would resolve to null and throw — the app would compile and then be dead
  /// on every screen for the whole M2→M10 role swap, which is precisely the
  /// window in which it most needs to be runnable and QA-able.
  ///
  /// This list becomes empty by construction at M12, when `packages/ui_kit` is
  /// deleted and this method and its import go with it.
  static Iterable<ThemeExtension<dynamic>> _legacyExtensions(ThemeData fork) =>
      fork.extensions.values;
}
