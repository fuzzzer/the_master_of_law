import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:themasteroflaw/src/src.dart';

/// Phase M · Unit A · **M13b — the T-0254 regression lock.**
///
/// Six call sites re-derived `FuzzzyCard(leadingRule:)`'s accent-card idiom as
/// a **per-side `Border` plus a `borderRadius`**. Flutter throws
/// `A borderRadius can only be given on borders with uniform colors` from
/// `paint()` when such a border has more than one *distinct visible* colour
/// (`box_border.dart:726-757`, SDK 3.32.0) — on the first frame, with no
/// interaction, on the app's core screens.
///
/// **Every static gate was green while this shipped**: `analyze` 0/0/2,
/// `flutter test` +14, the consumer guard 0 blocking, `flutter build bundle`
/// exit 0. It is a *paint-time* assertion, so only rendering a frame finds it.
/// That is precisely the hole this file plugs, and it plugs it twice:
///
/// 1. **A runtime lock** — [AppRuleCard] renders with a rule colour distinct
///    from `line` and must not throw. Proven able to fail by a negative control
///    that pumps the exact broken idiom and asserts it *does* throw.
/// 2. **A source lock** — no `BoxDecoration` in `lib/` may combine a
///    `borderRadius` with a per-side `Border(...)` carrying two or more
///    `BorderSide`s. This is the check that would have caught all six sites
///    before a device ever ran, and it is what stops the idiom coming back the
///    next time someone writes an accent card from memory.
///
/// 🔴 The source lock found **two sites the T-0254 ticket's own hand sweep
/// missed** (`case_risks_section` and `case_timeline_section`, both firing
/// unconditionally). A hand sweep of a bug class is a sample; a scanner is the
/// population. Do not replace this test with a re-read.
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

  group('AppRuleCard paints', () {
    testWidgets('with an accent rule distinct from `line` — T-0254', (
      tester,
    ) async {
      await pump(
        tester,
        Builder(
          builder: (context) {
            final colors = context.fuzzzyColors;
            return AppRuleCard(
              // `destructive` is the worst case: maximally distinct from
              // `line`, and the colour the cases list actually paints.
              rule: colors.destructive,
              borderRadius: context.fuzzzyRadius.l,
              padding: context.fuzzzyDensity.card,
              child: const Text('ფაქტი'),
            );
          },
        ),
      );
      expect(
        tester.takeException(),
        isNull,
        reason:
            'AppRuleCard must never combine a non-uniform Border with a '
            'borderRadius — that is the T-0254 throw',
      );
      expect(find.text('ფაქტი'), findsOneWidget);
    });

    testWidgets('with rule == `line` (the resolved-tile state)', (
      tester,
    ) async {
      // The state-dependent half of T-0254: `case_tasks_section` only threw
      // when NOT resolved, because the resolved state made both colours
      // `line` — one distinct visible colour — and painted fine. A pass that
      // screenshots only the resolved state sees nothing.
      await pump(
        tester,
        Builder(
          builder: (context) => AppRuleCard(
            rule: context.fuzzzyColors.line,
            ruleWidth: 3,
            borderRadius: context.fuzzzyRadius.m,
            padding: context.fuzzzyDensity.tile,
            child: const Text('კითხვა'),
          ),
        ),
      );
      expect(tester.takeException(), isNull);
    });

    testWidgets('the box border is UNIFORM while a radius is present', (
      tester,
    ) async {
      await pump(
        tester,
        Builder(
          builder: (context) => AppRuleCard(
            rule: context.fuzzzyColors.destructive,
            borderRadius: context.fuzzzyRadius.l,
            padding: context.fuzzzyDensity.card,
            child: const Text('x'),
          ),
        ),
      );
      final decorated = tester
          .widgetList<Container>(find.byType(Container))
          .map((c) => c.decoration)
          .whereType<BoxDecoration>()
          .where((d) => d.borderRadius != null)
          .toList();
      expect(decorated, isNotEmpty);
      for (final d in decorated) {
        expect(
          d.border!.isUniform,
          isTrue,
          reason:
              'a BoxDecoration carrying a borderRadius must have a uniform '
              'border, or Flutter throws during paint()',
        );
      }
    });

    testWidgets('NEGATIVE CONTROL: the old idiom really does throw', (
      tester,
    ) async {
      // A test that has never been seen to fail is not evidence. This pumps
      // exactly what `case_card.dart:56` carried before M13b.
      await pump(
        tester,
        Builder(
          builder: (context) {
            final colors = context.fuzzzyColors;
            return Container(
              padding: context.fuzzzyDensity.card,
              decoration: BoxDecoration(
                color: colors.surface,
                borderRadius: BorderRadius.circular(context.fuzzzyRadius.l),
                border: Border(
                  left: BorderSide(color: colors.destructive, width: 4),
                  top: BorderSide(color: colors.line),
                  right: BorderSide(color: colors.line),
                  bottom: BorderSide(color: colors.line),
                ),
              ),
              child: const Text('x'),
            );
          },
        ),
      );
      final thrown = tester.takeException();
      expect(
        thrown,
        isNotNull,
        reason:
            'if this stops throwing, the SDK changed and the source lock below '
            'may be over-strict — re-read box_border.dart before relaxing it',
      );
      expect(thrown.toString(), contains('uniform colors'));
    });
  });

  test(
    'no BoxDecoration in lib/ combines a borderRadius with a multi-side Border',
    () {
      final offenders = _multiSideBorderWithRadius();
      expect(
        offenders,
        isEmpty,
        reason:
            'These sites throw "A borderRadius can only be given on borders '
            'with uniform colors" during paint() as soon as two of their '
            'sides carry different colours (T-0254):\n'
            '  ${offenders.join('\n  ')}\n'
            'Use AppRuleCard (uniform Border.all + a ClipRRect-clipped rule '
            'overlay), which is the kit FuzzzyCard idiom. A single-side '
            'Border(top: …) plus a radius is LEGAL and is not reported here.',
      );
    },
  );
}

/// Every `path:line` in `lib/` whose `BoxDecoration` carries **both** a
/// `borderRadius:` and a `border: Border(` with two or more `BorderSide(`s.
///
/// Deliberately reports on *side count*, not on distinct colours: two sides of
/// the same colour is legal today but is one edit away from the throw, and a
/// source scanner cannot resolve a role to a colour anyway. Eight single-side
/// `Border(…)` + radius sites exist in this app and are correctly ignored.
List<String> _multiSideBorderWithRadius() {
  final out = <String>[];
  final files = Directory('lib')
      .listSync(recursive: true)
      .whereType<File>()
      .where((f) => f.path.endsWith('.dart'));

  for (final f in files) {
    final src = f.readAsStringSync();
    for (final m in RegExp(r'BoxDecoration\(').allMatches(src)) {
      final body = src.substring(m.end - 1, _closeParen(src, m.end - 1));
      if (!body.contains('borderRadius:')) continue;
      final b = RegExp(r'border:\s*Border\(').firstMatch(body);
      if (b == null) continue;
      final borderBody = body.substring(
        b.end - 1,
        _closeParen(body, b.end - 1),
      );
      if (RegExp(r'BorderSide\(').allMatches(borderBody).length < 2) continue;
      final line = '\n'.allMatches(src.substring(0, m.start)).length + 1;
      out.add('${f.path}:$line');
    }
  }
  out.sort();
  return out;
}

/// Index just past the `)` matching the `(` at [open].
int _closeParen(String src, int open) {
  var depth = 0;
  for (var i = open; i < src.length; i++) {
    if (src[i] == '(') depth++;
    if (src[i] == ')') {
      depth--;
      if (depth == 0) return i + 1;
    }
  }
  return src.length;
}
