import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
// The `context.fuzzzyTextStyles` role accessor is an extension declared in the
// kit; an extension only applies where it is imported, so without this line
// the three role assertions below do not compile.
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:go_router/go_router.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:themasteroflaw/src/src.dart';

/// Phase M · Unit A · **M16 — the `T-0259` regression lock.**
///
/// S9's code review found the run's own central argument un-applied to the
/// app's primary navigation: `_bottomNav` set **both** `selectedLabelStyle` and
/// `unselectedLabelStyle` to `fuzzzyTextStyles.label` — Space Mono, 11 pt,
/// `w400`, `letterSpacing: 1.76`, the **Latin-only uppercase eyebrow** role —
/// on four Georgian labels, against `USING.md:354` rule 5b, which names
/// *"nav item"* as a `control` consumer in as many words.
///
/// It cost two things at once, and the second is a defect under
/// `PLAN_PHASE_M` §4 rather than an expected change:
///
/// 1. **The typeface.** Space Mono has no Georgian block, so all four labels
///    fell through `fontFamilyFallback` and picked up 1.76 px of tracking per
///    Mkhedruli glyph. This is the *identical* defect that justified building
///    [AppStatusChip] rather than adopting `FuzzzyStatusChip`
///    (`PHASE_M_KIT_QUEUE` item 11) — and `test/app_status_chip_test.dart`
///    locks it **for one chip** while the nav bar violated it on every screen.
///    An invariant tested in one place and broken in another is not an
///    invariant, which is why this file exists at all.
/// 2. **The selection state.** The fork
///    (`782c4e7:packages/ui_kit/lib/src/themes/ui_kit_theme.dart:64-73` and
///    `:138-147`) ran `w600` selected against `w400` unselected. Both roles
///    became `label`, i.e. `w400` / `w400`, so **tapping a tab changed no type
///    weight** — leaving colour and the filled `activeIcon` as the only
///    feedback, on a deliberately monochrome palette.
///
/// ## Two mechanisms this file pins that no screenshot diff can see
///
/// 🔴 **The size step was never real, and must not be "restored".**
/// `bottom_navigation_bar.dart:900-906` `_effectiveTextStyle` prefers a
/// non-null `fontSize` on the *style* over the `selectedFontSize` /
/// `unselectedFontSize` parameters. Every kit type role carries a `fontSize`,
/// so Material's 14/12 defaults are unreachable here and `_Label:711-712,728`
/// computes its scale `Tween` from the style sizes — ratio 1.0, animation
/// inert. That is **not** a shortfall against the fork: the fork pinned
/// `fontSize: 12` on *both* states, so its scale animation was inert too. The
/// step that existed was weight, and weight is what is asserted below.
/// Adding `selectedFontSize:` to the theme would be pure dead configuration
/// (the `T-0262` failure mode) — it can never be read.
///
/// 🔴 **`textScaler` is not an axis on this widget.**
/// `bottom_navigation_bar.dart:758` wraps every label in
/// `MediaQuery.withClampedTextScaling(maxScaleFactor: 1.0, …)`, so nav labels
/// do **not** grow at accessibility text sizes — Material shows a tooltip
/// instead. The matrix group below still runs all six M14 points, but the cell
/// that actually carries risk is `1.0`: the role change is a **23 % width
/// increase at every scale** (11 pt → 13.5 pt) inside a fixed four-tile row
/// that is only ~90 dp wide per tile at 360 dp. That widening is real,
/// permanent, and invisible to the textScaler axis — so it gets its own
/// assertion rather than being assumed safe.
///
/// The bar is driven through the **real [MainShell]** on a real
/// `StatefulShellRoute`, not a hand-copied `BottomNavigationBar`: a copy would
/// keep passing if someone changed the four Georgian labels or the shell's
/// structure, which is exactly the drift this lock is meant to catch.
void main() {
  // See theme_roles_test.dart for why these lines are narrowing, not weakening.
  TestWidgetsFlutterBinding.ensureInitialized();
  GoogleFonts.config.allowRuntimeFetching = false;

  final unexpectedZoneErrors = <Object>[];
  bool isFontLoaderNoise(Object e) {
    final s = e.toString();
    return s.contains('allowRuntimeFetching') ||
        s.contains('Failed to load font');
  }

  setUp(unexpectedZoneErrors.clear);
  tearDown(() => expect(unexpectedZoneErrors, isEmpty));

  /// The four labels `main_shell.dart` actually ships, in tab order. Used only
  /// to *locate* the rendered `Text`s — the widget under test supplies them.
  const labels = <String>['საქმეები', 'ჩატი', 'კანონები', 'პროფილი'];

  GoRouter buildRouter() => GoRouter(
    initialLocation: '/tab0',
    routes: [
      StatefulShellRoute.indexedStack(
        builder: (context, state, shell) => MainShell(navigationShell: shell),
        branches: [
          for (var i = 0; i < labels.length; i++)
            StatefulShellBranch(
              routes: [
                GoRoute(
                  path: '/tab$i',
                  builder: (_, _) => const SizedBox.shrink(),
                ),
              ],
            ),
        ],
      ),
    ],
  );

  /// Pump the real shell at an exact logical viewport and textScaler,
  /// returning **every** layout error the frame produced.
  ///
  /// Same idiom, and the same reasons, as `case_section_overflow_test.dart`:
  /// `devicePixelRatio: 1` + an explicit `physicalSize` is the widget-test
  /// equivalent of the device recipe `wm density 160; wm size <W>x800`, and
  /// chaining `FlutterError.onError` (never replacing it) collects all errors
  /// instead of only the first while still letting `flutter_test`'s own
  /// handler complete the pipeline.
  Future<List<String>> pumpShell(
    WidgetTester tester, {
    required double width,
    required double scale,
  }) async {
    final layoutErrors = <String>[];
    final previousOnError = FlutterError.onError;
    FlutterError.onError = (details) {
      FlutterError.dumpErrorToConsole(details, forceReport: true);
      layoutErrors.add('${details.exception}');
      previousOnError?.call(details);
    };
    addTearDown(() => FlutterError.onError = previousOnError);

    tester.view.devicePixelRatio = 1.0;
    tester.view.physicalSize = Size(width, 800);
    addTearDown(tester.view.reset);

    late ThemeData theme;
    runZonedGuarded(
      () => theme = ThemasteroflawTheme.dark(),
      (e, _) {
        if (!isFontLoaderNoise(e)) unexpectedZoneErrors.add(e);
      },
    );

    await tester.pumpWidget(
      MaterialApp.router(
        theme: theme,
        routerConfig: buildRouter(),
        builder: (context, child) => MediaQuery(
          data: MediaQueryData(
            size: Size(width, 800),
            textScaler: TextScaler.linear(scale),
          ),
          child: child!,
        ),
      ),
    );
    await tester.pumpAndSettle();
    return layoutErrors;
  }

  /// The style Material actually paints a nav label with.
  ///
  /// It is **not** on the `Text` widget — `_Label` builds a bare
  /// `Text(item.label!)` and supplies the style through a
  /// `DefaultTextStyle.merge` above it (`:715-719`), lerped between the
  /// unselected and selected styles by the tile's animation. So reading
  /// `Text.style` would return `null` and any assertion on it would be
  /// vacuously true — the exact shape of bug this file guards against.
  TextStyle paintedStyle(WidgetTester tester, String label) =>
      DefaultTextStyle.of(tester.element(find.text(label))).style;

  group('T-0259 · nav labels take a Georgian-capable control role', () {
    testWidgets('never the mono `label` eyebrow role, on any tab', (
      tester,
    ) async {
      expect(await pumpShell(tester, width: 360, scale: 1), isEmpty);

      final ctx = tester.element(find.text(labels.first));
      final type = ctx.fuzzzyTextStyles;

      // 🔴 `control` and `bodyS` do NOT share one `fontFamily` string. The kit
      // resolves its roles through GoogleFonts, which registers **one family
      // per weight**, so the two roles land as `Inter_600` and `Inter_regular`
      // — same typeface, different registered name. (This is also why
      // `_georgianize` has to resolve Noto Sans Georgian per weight rather
      // than adding one blanket fallback.) Asserting a single expected family
      // for all four tabs is therefore wrong; what matters is that every tab
      // is painted in one of the two Inter roles and never in the mono
      // eyebrow.
      final interRoles = {type.control.fontFamily, type.bodyS.fontFamily};

      for (final label in labels) {
        final painted = paintedStyle(tester, label);
        expect(
          interRoles,
          contains(painted.fontFamily),
          reason:
              '"$label" must be painted in `control` or `bodyS` — USING.md:354 '
              'rule 5b names "nav item" explicitly. Got ${painted.fontFamily}',
        );
        expect(
          painted.fontFamily,
          isNot(type.label.fontFamily),
          reason:
              '`label` is the MONO uppercase eyebrow role. Space Mono has no '
              'Georgian block, so "$label" would silently fall to a platform '
              'face at platform metrics — the same defect AppStatusChip was '
              'built to avoid, and the one that invalidates the M14 gate',
        );
        expect(
          painted.letterSpacing ?? 0.0,
          isNot(type.label.letterSpacing),
          reason:
              '1.76px of eyebrow tracking must not be bolted onto Mkhedruli',
        );
        expect(
          painted.fontFamilyFallback,
          isNotEmpty,
          reason:
              'the app-side Georgian fallback (kit-queue item 6) must survive '
              'onto the nav bar, exactly as theme_roles_test invariant 2 '
              'requires of every role',
        );
      }
    });

    testWidgets('selection still has a WEIGHT step, not colour alone', (
      tester,
    ) async {
      expect(await pumpShell(tester, width: 360, scale: 1), isEmpty);

      final ctx = tester.element(find.text(labels.first));
      final type = ctx.fuzzzyTextStyles;

      // Tab 0 is the initial location, so it is the selected one and its
      // tile's animation has already settled at 1.0.
      final selected = paintedStyle(tester, labels[0]);
      final unselected = paintedStyle(tester, labels[1]);

      expect(
        selected.fontWeight,
        type.control.fontWeight,
        reason: 'the selected tab must be `control` (w600)',
      );
      expect(
        unselected.fontWeight,
        type.bodyS.fontWeight,
        reason: 'an unselected tab must be `bodyS` (w400)',
      );
      expect(
        selected.fontWeight,
        isNot(unselected.fontWeight),
        reason:
            'PLAN_PHASE_M §4 lists "a state losing distinct feedback" as a '
            'DEFECT. The fork stepped w600 -> w400; both became w400 at M1 '
            'and nothing but colour distinguished the tabs (T-0259)',
      );
      // Both roles share bodyS metrics, so the step is weight and nothing
      // else. Pinned so a future "let us also grow it" edit has to argue with
      // the file header rather than land silently.
      expect(selected.fontSize, unselected.fontSize);
    });

    testWidgets('tapping a tab MOVES the weight step to the tapped tab', (
      tester,
    ) async {
      expect(await pumpShell(tester, width: 360, scale: 1), isEmpty);

      final ctx = tester.element(find.text(labels.first));
      final type = ctx.fuzzzyTextStyles;

      await tester.tap(find.text(labels[2]));
      await tester.pumpAndSettle();

      // The live behaviour the ticket describes: this is what a user sees, and
      // it is what was broken. A static style assertion alone would pass on a
      // bar whose selection never moved.
      expect(paintedStyle(tester, labels[2]).fontWeight, type.control.fontWeight);
      expect(paintedStyle(tester, labels[0]).fontWeight, type.bodyS.fontWeight);
    });
  });

  /// 🔴 **This group is a STRUCTURAL guard, and explicitly NOT a truncation
  /// gate. Read this before quoting it as one.**
  ///
  /// 11 pt → 13.5 pt is a permanent ~23 % width increase on four Georgian
  /// labels in a fixed four-tile row (~90 dp per tile at 360 dp), so the
  /// obvious question is whether the wider role now truncates them. **A widget
  /// test cannot answer that**, for two independent reasons that were both
  /// measured here rather than assumed:
  ///
  /// 1. **A `BottomNavigationBar` cannot raise a `RenderFlex overflow` from
  ///    label width at all.** Negative control, run at M16: `_bottomNav` was
  ///    temporarily pointed at `titleL` — **24 pt**, nearly double the shipped
  ///    role — and all six cells below stayed **green**. The label sits under
  ///    an `Align` inside a fixed-width tile, so it is clipped or ellipsised
  ///    silently; nothing is ever thrown. This is the same structural blindness
  ///    `T-0264` names for the workspace header, in miniature: **a zero-hit
  ///    layout gate is not a truncation gate**, and no amount of it on this
  ///    widget ever will be.
  /// 2. **The test font over-predicts truncation, so a geometric assertion
  ///    would fail on correct code.** `flutter test` runs with
  ///    `--use-test-fonts --disable-asset-fonts` — a fixed-advance face where
  ///    one glyph is one `fontSize` wide. Measured at 360 dp on the shipped
  ///    roles: `საქმეები` and `კანონები` want **108.0 px** of natural width in
  ///    a **90.0 px** box, and `პროფილი` wants 94.5. The *old* 11 pt mono role
  ///    computes to ~102 px in the same font, i.e. **also** over budget — so
  ///    this font says both the defect and the fix truncate, and can therefore
  ///    distinguish neither. Noto Sans Georgian is substantially narrower than
  ///    the test face (JOURNAL M14d: a row that overflowed 2.9 px on the device
  ///    overflowed 111 px here).
  ///
  /// **Consequence, and it is a real one:** whether the wider role fits on a
  /// real 360 dp screen is a **device** question, and it is answered by the
  /// M20 re-run cells, not by this file. If it does not fit, `T-0259`'s fix
  /// would trade a lost weight step for a truncated nav label — one defect for
  /// another — and that must be caught in a screenshot, by eye.
  ///
  /// What the six cells below *do* still buy: they prove the shell lays out
  /// with no layout assertion at every matrix point and still renders all four
  /// labels, which catches a future structural break (a nav wrapped in a `Row`
  /// that genuinely can overflow, or a label silently dropped).
  group('T-0259 · the shell still lays out, and keeps all four labels', () {
    const cells = <(double, double)>[
      (1.0, 360), // ← the tightest tile: ~90 dp each
      (1.0, 599),
      (1.0, 601),
      (1.3, 360),
      (1.3, 599),
      (1.3, 601),
    ];

    for (final (scale, width) in cells) {
      testWidgets('textScaler $scale · ${width.toInt()} dp', (tester) async {
        final errors = await pumpShell(tester, width: width, scale: scale);
        tester.takeException();
        expect(
          errors,
          isEmpty,
          reason:
              'M14 gate: no RenderFlex overflow / layout assertion is allowed '
              'in any matrix cell. (Structural only — see the group doc: this '
              'assertion is blind to label truncation.)\n  ${errors.join('\n  ')}',
        );
        // All four labels must still be *present*; a bar that solved its own
        // width problem by dropping labels would pass the overflow assertion.
        for (final label in labels) {
          expect(find.text(label), findsOneWidget, reason: 'missing: $label');
        }
      });
    }
  });
}
