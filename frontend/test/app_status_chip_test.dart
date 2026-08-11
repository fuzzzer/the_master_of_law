import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:themasteroflaw/src/src.dart';

/// Phase M · Unit A · M11c.
///
/// [AppStatusChip] replaced **five byte-identical app-side copies** of
/// `FuzzzyStatusChip`'s recipe. It exists for exactly one reason: the kit
/// widget renders `fuzzzyTextStyles.label.toUpperCase()` — the mono, Latin-only
/// eyebrow role — and every label in this app is Georgian
/// (`PHASE_M_KIT_QUEUE` item 11).
///
/// **That reason is the thing this file locks.** `analyze` cannot see it, a
/// screenshot diff would not catch a silent `toUpperCase()` on Mkhedruli
/// (it is a unicase script, so the string is unchanged — only the *font* is
/// wrong), and the failure mode is exactly the one that would invalidate the
/// M14 overflow gate: Georgian rendered in a face the kit does not control.
///
/// When kit item 11 lands and `AppStatusChip` is deleted, **this file goes with
/// it** — do not keep it pointed at the kit widget without re-reading what it
/// asserts.
void main() {
  // See theme_roles_test.dart for why all three of these lines are mandatory
  // and are narrowing, not weakening.
  TestWidgetsFlutterBinding.ensureInitialized();
  GoogleFonts.config.allowRuntimeFetching = false;

  final unexpectedZoneErrors = <Object>[];
  bool isFontLoaderNoise(Object e) {
    final s = e.toString();
    return s.contains('allowRuntimeFetching') ||
        s.contains('Failed to load font');
  }

  Future<void> pump(WidgetTester tester, Widget child) async {
    late ThemeData theme;
    runZonedGuarded(
      () => theme = ThemasteroflawTheme.dark(),
      (e, _) {
        if (!isFontLoaderNoise(e)) unexpectedZoneErrors.add(e);
      },
    );
    await tester.pumpWidget(
      MaterialApp(
        theme: theme,
        home: Scaffold(body: Center(child: child)),
      ),
    );
  }

  setUp(unexpectedZoneErrors.clear);
  tearDown(() => expect(unexpectedZoneErrors, isEmpty));

  const georgian = 'დადასტურებული';

  testWidgets('renders the Georgian label EXACTLY as given', (tester) async {
    await pump(
      tester,
      const AppStatusChip(label: georgian, kind: AppStatusKind.success),
    );
    // The whole point of the widget. `toUpperCase()` on Mkhedruli is a no-op,
    // so an equality check on the string alone would pass even against the kit
    // widget — the style assertion below is what actually distinguishes them.
    expect(find.text(georgian), findsOneWidget);
  });

  testWidgets('labels in `control`, never the mono `label` eyebrow role', (
    tester,
  ) async {
    await pump(
      tester,
      const AppStatusChip(label: georgian, kind: AppStatusKind.success),
    );
    final rendered = tester.widget<Text>(find.text(georgian)).style!;
    final ctx = tester.element(find.text(georgian));
    final type = ctx.fuzzzyTextStyles;

    expect(
      rendered.fontFamily,
      type.control.fontFamily,
      reason: 'the label must take `control`, the Georgian-capable role',
    );
    expect(
      rendered.fontFamily,
      isNot(type.label.fontFamily),
      reason:
          '`label` is the MONO eyebrow role — Space Mono has no Georgian '
          'block, so this would silently fall to a platform face at platform '
          'metrics and invalidate the M14 overflow gate',
    );
    // Every kit type role carries the Georgian fallback (theme_roles_test.dart
    // invariant 2); losing it here would be the same defect by another route.
    expect(rendered.fontFamilyFallback, isNotEmpty);
  });

  testWidgets('every kind resolves to a role, and none of them throws', (
    tester,
  ) async {
    for (final kind in AppStatusKind.values) {
      await pump(tester, AppStatusChip(label: georgian, kind: kind));
      expect(find.text(georgian), findsOneWidget, reason: 'kind: $kind');
    }
  });

  testWidgets("qaId produces the kit widget's own `chip.<id>` identifier", (
    tester,
  ) async {
    await pump(
      tester,
      const AppStatusChip(
        label: georgian,
        kind: AppStatusKind.neutral,
        qaId: 'trust.x1',
      ),
    );
    // Deliberately the SAME string the kit's FuzzzyStatusChip emits, so saved
    // QA scripts survive the eventual swap to it. A `Semantics` without
    // `container: true` would merge into the parent and make this unreachable
    // (RECIPE_NEW_WIDGET §5.1) — this is the runtime check that catches it.
    expect(find.byKey(const Key('chip.trust.x1')), findsOneWidget);
    final node = tester.getSemantics(find.byKey(const Key('chip.trust.x1')));
    expect(node.identifier, 'chip.trust.x1');
  });
}
