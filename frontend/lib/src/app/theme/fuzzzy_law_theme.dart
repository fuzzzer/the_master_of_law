import 'package:flutter/material.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:google_fonts/google_fonts.dart';

/// Fuzzzy Law — the ONE bridge from `fuzzzy_ui_kit` to Flutter's
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
/// **No longer transitional.** M1–M11 kept the fork's own `UiColors` /
/// `UiTextStyles` / `UiFormStyles` extensions attached alongside the kit's, so
/// that a not-yet-migrated `context.uiColors` read would still resolve instead
/// of throwing mid-swap. **M12 deleted `packages/ui_kit` and that bridge with
/// it** (together with its tripwire group in `test/theme_roles_test.dart`).
/// This class is now the app's only source of `ThemeData`, and every value in
/// it comes from `fuzzzy_ui_kit` or from [LegalDomainColors].
abstract final class FuzzzyLawTheme {
  /// Ink · night skin. The app's default (the fork's dark mode).
  static ThemeData dark() => _build(FuzzzySkin.night);

  /// Ink · paper skin.
  static ThemeData light() => _build(FuzzzySkin.paper);

  /// The brand pack this build runs on. **`inkPack` unless overridden**, and
  /// the override exists for exactly one reason: `USING.md` §10 says a green
  /// guard cannot tell you whether a screen survives a pack swap, and M14 (S8)
  /// has to prove it does.
  ///
  /// ```bash
  /// fvm flutter run -t lib/main_development.dart --flavor development \
  ///   --dart-define=FUZZZY_PACK=stress
  /// ```
  ///
  /// Resolved through the kit's own `fuzzzyBrandPacks` map rather than an
  /// app-side `if`, so a pack added to the kit is reachable here with no edit.
  /// An unknown name falls back to `inkPack`: a typo in a QA command must not
  /// silently produce a third look nobody reviewed. **This getter is the whole
  /// pack-swap surface of the app** — every other file reads roles, which is
  /// exactly what makes one swap here sufficient.
  static FuzzzyBrandPack get pack =>
      fuzzzyBrandPacks[const String.fromEnvironment(
        'FUZZZY_PACK',
        defaultValue: 'ink',
      )] ??
      inkPack;

  static ThemeData _build(FuzzzySkin skin) {
    final base = FuzzzyTheme.build(pack, skin);

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
      bottomNavigationBarTheme: _bottomNav(colors, type),
      // 🔴 DO NOT write an explicit `<ThemeExtension<dynamic>>` type argument
      // on this list. `ThemeExtension` is F-bounded
      // (`class ThemeExtension<T extends ThemeExtension<T>>`), so a type
      // argument written HERE gets bound-normalised by the compiler front end
      // to `ThemeExtension<ThemeExtension<dynamic>>`, which then refuses every
      // spread of Flutter's own `Map<Object, ThemeExtension<dynamic>>.values`.
      // **`flutter analyze` does not report this; `flutter test`, `flutter run`
      // and `flutter build` all do** — see JOURNAL M10 §A. Leave the literal
      // untyped and let it infer from `copyWith`'s parameter, which Flutter
      // declares correctly.
      extensions: [
        ...base.extensions.values.where((e) => e is! FuzzzyTextStyles),
        type,
        // The app's own taxonomy palette — NOT a kit role, by owner ruling
        // (harvest/mol.md §3, MAPPING §2.1). Skin-bound like the fork's was.
        if (skin == FuzzzySkin.night)
          LegalDomainColors.dark
        else
          LegalDomainColors.light,
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

  /// **14 stock `AppBar` sites — 12 live, 2 in dead UI** (re-counted at M18,
  /// `T-0262`; the two are `questionnaire_page` / `questionnaire_review_page`,
  /// which S9 ruled dead code killed by commit `870d507` three months before
  /// Phase M — see the M18 deletion note above [_bottomNav]).
  ///
  /// Flat on `ground`, ink foreground, no scroll elevation — the Ink surface
  /// has no shadow vocabulary.
  ///
  /// **`titleM`, not `titleL` (corrected at M3).** `MAPPING.md` §3 judgement 1
  /// maps MoL's page headers to `titleM` on purpose: the app has no
  /// display-scale text, its AppBar titles were 16–20pt in the fork (three of
  /// the four in `features/profile` were `bodyBold16`), and every one of them
  /// is a long Georgian string. `titleL` is 24pt — a 50% jump on the 16pt
  /// titles, and the single row `MAPPING.md` flags as most likely to overflow
  /// at `textScaler 1.3` on a 360dp screen. `titleM` (18pt) sits inside the
  /// fork's own range and keeps the ratio to `titleS`/`body`.
  static AppBarTheme _appBar(FuzzzyColors c, FuzzzyTextStyles t) => AppBarTheme(
    backgroundColor: c.ground,
    foregroundColor: c.ink,
    surfaceTintColor: Colors.transparent,
    elevation: 0,
    scrolledUnderElevation: 0,
    centerTitle: false,
    titleTextStyle: t.titleM.copyWith(color: c.ink),
    iconTheme: IconThemeData(color: c.ink),
    actionsIconTheme: IconThemeData(color: c.ink),
  );

  /// **1 stock `Card` site** — `dev_panel_tile.dart:27`, and nothing else.
  ///
  /// This doc said **28** until M18 (`T-0262`). That was an M1-era count that
  /// was true when it was written and was never revised as M2–M11 deleted the
  /// call sites; a `grep` at M18 found one survivor. Left in place *because*
  /// it still configures a live surface — the dev panel, which S9's verifier
  /// reached and drove clean at 1.3/360 — and because a stock `Card` is the
  /// kind of thing a later change reintroduces without thinking.
  ///
  /// Material 3's default card is an elevated, tinted,
  /// shadow-casting surface; Ink cards are a flat `surface` panel with a
  /// hairline `line` border.
  ///
  /// **`radius.l`, not `radius.m` (corrected at M3).** `FuzzzyCard`
  /// (`containers/fuzzzy_card.dart:51-59`) and `USING.md` §5.1's copyable
  /// screen both build the surface rung at `radius.l`. Matching it is what
  /// makes a stock `Card` and a hand-rolled `surface` panel indistinguishable
  /// from a `FuzzzyCard` — the same reasoning [_input] already applies to
  /// fields. It is 1px in Ink and 8px in the stress pack, so it only shows up
  /// where it matters: under a pack swap.
  static CardThemeData _card(FuzzzyColors c, FuzzzyRadius r) => CardThemeData(
    color: c.surface,
    surfaceTintColor: Colors.transparent,
    shadowColor: Colors.transparent,
    elevation: 0,
    margin: EdgeInsets.zero,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(r.l),
      side: BorderSide(color: c.line),
    ),
  );

  /// **6 stock `Divider` sites — 5 live, 1 in dead UI** (re-counted at M18).
  ///
  /// `space: 1` is deliberate and is the one value here that is a dimension
  /// rather than a role: Material's default is **16**, i.e. a divider reserves
  /// 15 px of vertical air around its hairline. All six call sites supply
  /// their own `space.*` / `density.*` padding, so inheriting Material's 16
  /// would double-space every one of them. Collapsing the reserve to the
  /// hairline itself is what makes a stock `Divider()` interchangeable with a
  /// hand-drawn `line` border — the same reasoning [_card] and [_input] apply
  /// to radii. Called out here because the doc used to justify only the
  /// colour, which left the reader to assume `space: 1` was an oversight.
  ///
  /// Material 3 resolves a divider's colour from
  /// `colorScheme.outlineVariant` (which the kit binds to `lineStrong`), NOT
  /// from `ThemeData.dividerColor` — so without this, every hairline would be
  /// drawn one step too heavy.
  static DividerThemeData _divider(FuzzzyColors c) => DividerThemeData(
    color: c.line,
    thickness: 1,
    space: 1,
  );

  /// **18 stock `InputDecoration` sites — 16 live, 2 in dead UI** (re-counted
  /// at M18; the doc said 19). Mirrors `FuzzzyTextField`'s box exactly
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

  // ---------------------------------------------------------------------------
  // DELETED at M18 (`T-0262`): `_chip` / `chipTheme`.
  //
  // It claimed "13 stock `Chip` sites" and configured **zero**. That number was
  // an M1-era count; M9/M9b cleared the last Material chip, and a census at M18
  // found no `Chip`, `ChoiceChip`, `FilterChip`, `ActionChip` or `InputChip`
  // anywhere in `lib/` (the four `Chip(` matches a naive grep returns are a
  // private `_ActionChip` at `consultation_page.dart:1587`, which is an app
  // widget and reads roles directly). Every chip in this app is now
  // `AppStatusChip`, `AppDomainChip`, `AppCitationChip` or a kit widget, and
  // none of them reads `ChipThemeData`.
  //
  // 🔴 **Deleted rather than corrected, deliberately, because dead config here
  // was not neutral — it was loaded.** Its `labelStyle` and
  // `secondaryLabelStyle` were `type.label`: the mono, Latin-only, wide-tracked
  // eyebrow role. That is precisely the `T-0259` defect fixed in `_bottomNav`
  // one checkpoint ago, and precisely the reason `AppStatusChip` exists at all
  // (`PHASE_M_KIT_QUEUE` item 11). So the first person to add a Material `Chip`
  // to this Georgian app would have silently inherited a label rendered through
  // `fontFamilyFallback` at 1.76px of tracking per Mkhedruli glyph — and would
  // have inherited it from a theme whose doc-comment told them 13 other sites
  // already relied on it.
  //
  // Correcting the comment would have left the trap; correcting the role would
  // have left an unread, untested, unrenderable block that no gate can keep
  // honest. Removing it removes a wrong default, not a safety net: a future
  // Material chip now falls back to Material's own theme, which is visibly
  // un-Ink and therefore gets noticed.
  // ---------------------------------------------------------------------------

  /// 1 stock `BottomNavigationBar` site (`main_shell`, verified at M18).
  /// Selected item uses
  /// `ink` rather than a brand accent — Ink keeps navigation monochrome.
  ///
  /// **`control` / `bodyS`, NOT `label` (corrected at M16, `T-0259`).** The
  /// first cut of this method set *both* label styles to `t.label`, and that
  /// was wrong twice over:
  ///
  /// 1. **It broke `USING.md:354` rule 5b** — *"a bold control label — a
  ///    button, tab, chip, segment or **nav item** — uses `control`"* — and the
  ///    role's own doc-comment names `nav item` too. `label` is the *uppercase
  ///    wide-tracked mono eyebrow*: Space Mono, 11 pt, `letterSpacing: 1.76`,
  ///    and **Space Mono has no Georgian block**. All four labels here are
  ///    Georgian (`საქმეები` · `ჩატი` · `კანონები` · `პროფილი`), so they fell
  ///    to `fontFamilyFallback` with 1.76 px of tracking bolted onto every
  ///    Mkhedruli glyph. This is the *same* defect that justified building
  ///    [AppStatusChip] instead of adopting `FuzzzyStatusChip`, and
  ///    `test/app_status_chip_test.dart` already locks it for one chip — while
  ///    it was being violated app-wide, on the primary navigation.
  /// 2. **It flattened the selection state to colour alone.** The fork
  ///    (`782c4e7:packages/ui_kit/…/ui_kit_theme.dart:64-73,138-147`) used
  ///    `w600` selected against `w400` unselected; both were `t.label`, i.e.
  ///    `w400`, so tapping a tab changed no type weight at all. Under
  ///    `PLAN_PHASE_M` §4 *"a state losing distinct feedback"* is a **defect**,
  ///    not an expected change. `control` and `bodyS` share `bodyS` metrics and
  ///    differ **only** in weight — which is exactly the fork's step, restored
  ///    on roles.
  ///
  /// 🔴 **Why there is deliberately no `selectedFontSize`/`unselectedFontSize`
  /// here.** They would be dead configuration. Flutter 3.32.0
  /// `bottom_navigation_bar.dart:900-906` `_effectiveTextStyle` only falls back
  /// to those parameters when the style's own `fontSize` is **null**, and every
  /// kit type role carries a `fontSize`. So Material's 14/12 defaults never
  /// apply, `_Label:711-712` reads the *style* sizes, and the built-in
  /// selection **scale** animation is inert at ratio 1.0. That is not a
  /// shortfall against the fork: the fork pinned `fontSize: 12` on *both*
  /// states, so its scale animation was equally inert and the size step never
  /// existed on this app. Restoring one would be a new behaviour, and a 26 %
  /// type jump on four Georgian labels inside a 90 dp tile at `textScaler 1.3`
  /// is the last place to introduce one. Selection reads as **weight + colour +
  /// the filled `activeIcon`** — three signals, one more than the fork's two.
  ///
  /// Locked by `test/bottom_nav_roles_test.dart` — seen red on all three role
  /// and state assertions before the fix.
  ///
  /// 🔴 **What that lock does NOT cover, and where the answer lives.** 11 pt →
  /// 13.5 pt is a permanent ~23 % width increase on four Georgian labels in
  /// ~90 dp tiles at 360 dp. No widget test can say whether that truncates:
  /// a `BottomNavigationBar` label is clipped silently rather than overflowing
  /// (negative control at M16 — `titleL`, 24 pt, produced **zero** layout
  /// errors in all six matrix cells), and the fixed-advance test font
  /// over-predicts width badly enough that it calls both the defect and the
  /// fix too wide. **The device matrix at M20 is the authority for this one**,
  /// by eye, on a screenshot.
  static BottomNavigationBarThemeData _bottomNav(
    FuzzzyColors c,
    FuzzzyTextStyles t,
  ) => BottomNavigationBarThemeData(
    backgroundColor: c.surface,
    selectedItemColor: c.ink,
    unselectedItemColor: c.inkMute,
    selectedLabelStyle: t.control.copyWith(color: c.ink),
    unselectedLabelStyle: t.bodyS.copyWith(color: c.inkMute),
    type: BottomNavigationBarType.fixed,
    elevation: 0,
  );
}
