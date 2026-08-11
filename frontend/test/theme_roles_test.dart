import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:themasteroflaw/src/src.dart';

/// Phase M · Unit A · **the first test in this repo.**
///
/// `frontend/` had no `test/` directory at all, so `fvm flutter test` exited 1
/// with *"Test directory not found"* — the M10 gate (`analyze+test`) could
/// never have passed as ledgered. This file makes the gate real rather than
/// weakening it; M10's own definition is *"0 errors, tests green"*.
///
/// It locks the four invariants **this migration created**, each of which
/// fails silently or catastrophically and none of which `analyze` can see:
///
/// 1. Every kit extension the app reads is attached to BOTH skins. A missing
///    one turns every `context.fuzzzy*` — hundreds of sites — into a null-bang
///    crash on the first frame.
/// 2. Every type role carries the Georgian `fontFamilyFallback`. The Ink pack's
///    families have no Georgian block; losing the fallback drops every Georgian
///    glyph to a *platform* font with *platform* metrics, which would silently
///    invalidate the M14 overflow gate (RUN_BRIEF §4's red note).
/// 3. The six Material sub-themes MAPPING §7 identified are set. `FuzzzyTheme
///    .build` deliberately sets none of them, and ~80 stock-Material widgets in
///    this app inherit them.
/// 4. Ink's radii really did collapse to the 2/3/4 ramp — the single most
///    visible expected change, and the one a wrong pack argument would undo.
///
/// The kit consumer guard test (`design/GUARD_TEMPLATE.md`) lands beside this
/// one at **M13**, once M10b/M11/M12 have cleared the 14 remaining blocking
/// literals. Until then this file is the whole `test` gate — say so honestly.
void main() {
  // 🔴 Required, and not optional boilerplate. `ThemasteroflawTheme` resolves
  // the Georgian fallback through `GoogleFonts.notoSansGeorgian`, and that call
  // reaches `ServicesBinding.instance` to read the asset manifest. Building a
  // theme before the binding exists throws `checkInstance` from every test at
  // once. The theme must also be built INSIDE the test bodies, not at the top
  // level, because top-level initialisers run before this line.
  TestWidgetsFlutterBinding.ensureInitialized();

  // 🔴 Also required, and it is a genuine finding about the app, not test
  // plumbing. Neither Ink's families nor Noto Sans Georgian is bundled as an
  // asset: `GoogleFonts` fetches them over HTTP on first use and caches them on
  // the device. Under `flutter test` that fetch fails and THROWS out of
  // `ThemasteroflawTheme.dark()`. Turning runtime fetching off makes the
  // resolver fall back instead of throwing, which is exactly what happens on a
  // cold, offline device — see JOURNAL M10 §B for what M14 must check.
  GoogleFonts.config.allowRuntimeFetching = false;

  // `GoogleFonts` registers a font as a FIRE-AND-FORGET async side effect of
  // returning the (synchronous) TextStyle, so with fetching off it throws into
  // the zone AFTER the theme has already been built correctly. Unhandled zone
  // errors fail whichever test happens to be running.
  //
  // This absorbs THAT ONE failure and nothing else: any other error is kept and
  // asserted on inside every test, so the gate is not weakened — a real problem
  // still fails the run, it just fails with a useful message instead of a font
  // download.
  final unexpectedZoneErrors = <Object>[];
  bool isFontLoaderNoise(Object e) {
    final s = e.toString();
    return s.contains('allowRuntimeFetching') ||
        s.contains('Failed to load font');
  }

  ThemeData buildTheme(ThemeData Function() build) {
    late ThemeData built;
    runZonedGuarded(
      () => built = build(),
      (e, _) {
        if (!isFontLoaderNoise(e)) unexpectedZoneErrors.add(e);
      },
    );
    return built;
  }

  final builders = <String, ThemeData Function()>{
    'dark (night)': ThemasteroflawTheme.dark,
    'light (paper)': ThemasteroflawTheme.light,
  };

  builders.forEach((name, build) {
    group(name, () {
      late ThemeData theme;
      setUp(() {
        unexpectedZoneErrors.clear();
        theme = buildTheme(build);
      });
      tearDown(() => expect(unexpectedZoneErrors, isEmpty));

      test('carries every kit extension the app reads', () {
        // The seven `context.fuzzzy*` getters used across lib/.
        expect(
          theme.extension<FuzzzyColors>(),
          isNotNull,
          reason: 'context.fuzzzyColors',
        );
        expect(
          theme.extension<FuzzzyTextStyles>(),
          isNotNull,
          reason: 'context.fuzzzyTextStyles',
        );
        expect(
          theme.extension<FuzzzySpace>(),
          isNotNull,
          reason: 'context.fuzzzySpace',
        );
        expect(
          theme.extension<FuzzzyRadius>(),
          isNotNull,
          reason: 'context.fuzzzyRadius',
        );
        expect(
          theme.extension<FuzzzyDensity>(),
          isNotNull,
          reason: 'context.fuzzzyDensity',
        );
        expect(
          theme.extension<FuzzzyMotion>(),
          isNotNull,
          reason: 'context.fuzzzyMotion',
        );
        expect(
          theme.extension<FuzzzyFormStyles>(),
          isNotNull,
          reason: 'context.fuzzzyFormStyles',
        );
      });

      test('every type role can render Georgian', () {
        final t = theme.extension<FuzzzyTextStyles>()!;
        final roles = <String, TextStyle>{
          'displayXl': t.displayXl,
          'displayL': t.displayL,
          'titleL': t.titleL,
          'titleM': t.titleM,
          'titleS': t.titleS,
          'body': t.body,
          'bodyS': t.bodyS,
          'control': t.control,
          'label': t.label,
          'data': t.data,
          'dataS': t.dataS,
          'dataL': t.dataL,
        };
        roles.forEach((role, style) {
          expect(
            style.fontFamilyFallback,
            isNotEmpty,
            reason:
                'type.$role has no fontFamilyFallback — Georgian would fall '
                'through to a platform font with platform metrics, and the '
                'M14 overflow gate would be certifying a typeface the kit '
                'does not control.',
          );
        });
      });

      test('the FIVE Material sub-themes with live call sites are set', () {
        // MAPPING §7: FuzzzyTheme.build sets none of these, and the stock
        // widgets in this app inherit them. Losing any one is invisible to
        // `analyze` and to every role count.
        //
        // Counts re-measured at M18 (`T-0262`) — the doc-comments in
        // `themasteroflaw_theme.dart` used to carry M1-era numbers:
        //   appBar 14 (12 live) · card 1 · divider 6 (5 live) ·
        //   input 18 (16 live) · bottomNav 1
        expect(theme.appBarTheme.backgroundColor, isNotNull);
        expect(theme.cardTheme.color, isNotNull);
        expect(theme.dividerTheme.color, isNotNull);
        expect(theme.inputDecorationTheme.fillColor, isNotNull);
        expect(theme.bottomNavigationBarTheme.selectedItemColor, isNotNull);
      });

      test('`chipTheme` is deliberately NOT set — and stays that way', () {
        // 🔴 This assertion is inverted ON PURPOSE (M18, `T-0262`). `_chip`
        // was deleted, not corrected: it claimed 13 stock `Chip` sites and
        // configured **zero** (a census at M18 found no `Chip`/`ChoiceChip`/
        // `FilterChip`/`ActionChip`/`InputChip` in `lib/`), and its
        // `labelStyle` was `type.label` — the mono, Latin-only eyebrow role,
        // i.e. exactly the `T-0259` defect that had just been fixed in
        // `_bottomNav` and exactly the reason `AppStatusChip` exists.
        //
        // Dead config that is also WRONG is a loaded gun: the first person to
        // drop a Material `Chip` into this Georgian app would have inherited a
        // label at 1.76px of tracking per Mkhedruli glyph, from a theme whose
        // comment assured them 13 other sites already depended on it.
        //
        // If someone re-adds a `chipTheme`, this test fails and they have to
        // read the reason first — which is the entire point of putting the
        // absence under test rather than just deleting the code.
        expect(
          theme.chipTheme.backgroundColor,
          isNull,
          reason:
              'a chipTheme is back. Before restoring it: are there really '
              'stock Material chips now, and does the label take `control` '
              'rather than the Latin-only `label` role? See the M18 note in '
              'themasteroflaw_theme.dart.',
        );
      });

      test("radii are Ink's 2/3/4 ramp, not the fork's 8/12/16", () {
        final r = theme.extension<FuzzzyRadius>()!;
        expect(r.s, 2.0);
        expect(r.m, 3.0);
        expect(r.l, 4.0);
        expect(r.circle, greaterThan(100));
      });
    });
  });

  // The `transitional fork bridge (dies at M12)` group that used to sit here
  // was DELETED at M12, in the same commit as `packages/ui_kit` and the
  // `legacy.extensions.values` spread it guarded — which is exactly what it
  // was written to force. It was a tripwire, never an assertion about correct
  // behaviour, so it was removed rather than "fixed to pass".
}
