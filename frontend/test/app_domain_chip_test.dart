import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/rendering.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:google_fonts/google_fonts.dart';

/// Phase M · Unit A · **M17 — the `T-0261` consolidation lock.**
///
/// [AppDomainChip] replaced **two divergent private `_DomainChip` classes** —
/// same name, same shape, one in `case_card.dart` and one in
/// `case_workspace_page.dart`. S9's review found them differing in three ways,
/// and each of the three is asserted here so the pair cannot re-form:
///
/// 1. **Only one had the M14b ellipsis hardening.** The `case_card` copy was a
///    plain non-flex child of a `Row`, and `RenderFlex` hands non-flex children
///    `maxWidth: infinity` — so a long label there would have **overflowed**
///    where its twin ellipsed. Both directions of that guard are pumped below,
///    because the guard is conditional and a test of only one branch would
///    pass against a widget that had lost the other.
/// 2. **One took a `dotColor`, the other read the taxonomy itself.** A caller
///    could therefore pass a disc colour that did not match the domain it
///    labelled. The widget now resolves both from [LegalDomain], and the test
///    asserts the disc follows the domain rather than an argument.
/// 3. **Neither emitted a QA identifier**, so both were unreachable from a
///    Marionette script — which is why no device cell could ever have
///    addressed the very chips `T-0263` is about.
///
/// The parent-aware surface rule ([AppChipParent]) gets its own case: it was a
/// *comment* in two files plus a private enum in a third, and a wrong rung is
/// invisible on one skin, so it is exactly the kind of rule that rots unread.
void main() {
  // See theme_roles_test.dart: narrowing, not weakening.
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

  Future<void> pump(WidgetTester tester, Widget child) async {
    late ThemeData theme;
    runZonedGuarded(
      () => theme = FuzzzyLawTheme.dark(),
      (e, _) {
        if (!isFontLoaderNoise(e)) unexpectedZoneErrors.add(e);
      },
    );
    await tester.pumpWidget(
      MaterialApp(theme: theme, home: Scaffold(body: Center(child: child))),
    );
  }

  /// The chip's own box colour, read off the `Container` it paints.
  Color boxColorOf(WidgetTester tester) {
    final container = tester.widget<Container>(
      find
          .descendant(
            of: find.byType(AppDomainChip),
            matching: find.byType(Container),
          )
          .first,
    );
    return (container.decoration! as BoxDecoration).color!;
  }

  const domain = LegalDomain.criminal;

  testWidgets('the parent-aware surface rule picks OPPOSITE rungs', (
    tester,
  ) async {
    await pump(
      tester,
      const AppDomainChip(domain: domain, parent: AppChipParent.ground),
    );
    final onGround = boxColorOf(tester);
    final ctx = tester.element(find.byType(AppDomainChip));
    final colors = ctx.fuzzzyColors;
    expect(
      onGround,
      colors.surface,
      reason: 'a chip sitting ON `ground` chrome draws a `surface` box',
    );

    await pump(
      tester,
      const AppDomainChip(domain: domain, parent: AppChipParent.surface),
    );
    expect(
      boxColorOf(tester),
      colors.ground,
      reason: 'the SAME chip inside a `surface` card draws a `ground` box',
    );
    expect(
      colors.surface,
      isNot(colors.ground),
      reason:
          'if these two roles ever collapse, the assertions above go vacuous '
          'and the rule silently stops being tested',
    );
  });

  testWidgets('the label takes `control`, never the mono `label` eyebrow', (
    tester,
  ) async {
    await pump(
      tester,
      const AppDomainChip(domain: domain, parent: AppChipParent.ground),
    );
    final rendered = tester
        .widget<Text>(find.text(domain.shortLabelKa))
        .style!;
    final ctx = tester.element(find.text(domain.shortLabelKa));
    final type = ctx.fuzzzyTextStyles;

    expect(rendered.fontFamily, type.control.fontFamily);
    expect(
      rendered.fontFamily,
      isNot(type.label.fontFamily),
      reason:
          'Space Mono has no Georgian block — the same defect AppStatusChip '
          'and the M16 nav fix exist for',
    );
    expect(rendered.fontFamilyFallback, isNotEmpty);
  });

  testWidgets('the disc follows the DOMAIN, not a caller-supplied colour', (
    tester,
  ) async {
    // The old `case_card` copy took `dotColor` as an argument, so nothing
    // stopped a caller pairing one domain's label with another's colour.
    for (final d in [LegalDomain.criminal, LegalDomain.tax]) {
      await pump(
        tester,
        AppDomainChip(domain: d, parent: AppChipParent.ground),
      );
      final ctx = tester.element(find.byType(AppDomainChip));
      // The 8 px disc is the only tightly-sized box in the widget; the outer
      // chip box has no size constraints of its own.
      final dot = tester.widget<Container>(
        find
            .descendant(
              of: find.byType(AppDomainChip),
              matching: find.byWidgetPredicate(
                (w) => w is Container && w.constraints?.maxWidth == 8.0,
              ),
            )
            .first,
      );
      expect(
        (dot.decoration! as BoxDecoration).color,
        ctx.legalDomainColors.of(d),
        reason: 'disc must be the taxonomy colour OF $d',
      );
    }
  });

  group('the M14b ellipsis guard — BOTH branches, at both call sites', () {
    testWidgets('BOUNDED parent: the label gives ground and ellipses', (
      tester,
    ) async {
      await pump(
        tester,
        const SizedBox(
          // Deliberately far too narrow for any Georgian short label.
          width: 60,
          child: Row(
            children: [
              Flexible(
                child: AppDomainChip(
                  domain: domain,
                  parent: AppChipParent.ground,
                ),
              ),
            ],
          ),
        ),
      );
      expect(tester.takeException(), isNull);
      final rp = tester.renderObject<RenderParagraph>(
        find.text(domain.shortLabelKa),
      );
      expect(
        rp.didExceedMaxLines,
        isTrue,
        reason:
            'given a bounded width the label must ellipse rather than '
            'overflow — this is the branch case_card was MISSING',
      );
    });

    testWidgets('UNBOUNDED parent: no Flexible, and nothing throws', (
      tester,
    ) async {
      // A plain (non-flex) child of a `Row` receives `maxWidth: infinity`, and
      // a `Flexible` under unbounded main-axis constraints THROWS. This is the
      // branch that makes the widget safe at every call site, and the reason
      // the guard is a `LayoutBuilder` rather than an unconditional `Flexible`.
      await pump(
        tester,
        const Row(
          children: [
            AppDomainChip(domain: domain, parent: AppChipParent.surface),
            Spacer(),
          ],
        ),
      );
      expect(
        tester.takeException(),
        isNull,
        reason: 'an unconditional Flexible would throw here',
      );
      final rp = tester.renderObject<RenderParagraph>(
        find.text(domain.shortLabelKa),
      );
      expect(
        rp.didExceedMaxLines,
        isFalse,
        reason: 'unconstrained, the chip takes its natural width as before',
      );
    });
  });

  testWidgets('qaId emits the same `chip.<id>` identifier as its siblings', (
    tester,
  ) async {
    await pump(
      tester,
      const AppDomainChip(
        domain: domain,
        parent: AppChipParent.ground,
        qaId: 'workspaceDomain',
      ),
    );
    // Deliberately the SAME shape AppStatusChip, AppCitationChip and the kit's
    // own chips emit, so one saved QA script addresses all of them. Neither
    // `_DomainChip` had any identifier at all, which is why the two chips
    // T-0263 is about were unaddressable from every device cell in this run.
    expect(find.byKey(const Key('chip.workspaceDomain')), findsOneWidget);
    final node = tester.getSemantics(
      find.byKey(const Key('chip.workspaceDomain')),
    );
    expect(node.identifier, 'chip.workspaceDomain');
  });

  testWidgets('no qaId ⇒ no identifier and no stray Key', (tester) async {
    await pump(
      tester,
      const AppDomainChip(domain: domain, parent: AppChipParent.ground),
    );
    expect(find.byKey(const Key('chip.null')), findsNothing);
  });

  /// **`T-0263` — the derived header height.**
  ///
  /// `case_workspace_page._headerHeight` reserves space for a row of these
  /// chips, replacing a hardcoded `Size.fromHeight(80)`. It derives the chip's
  /// line box with a `TextPainter` over `type.control` rather than computing
  /// `fontSize × height × scaler`, because **that formula is wrong**: it
  /// predicts 34.25 px for a chip that really renders 24.80.
  ///
  /// This group is the load-bearing check on that decision. If the identity
  /// below ever breaks, the AppBar silently under- or over-reserves — which is
  /// the whole class of bug the literal `80` was (3 px short at 1.3, and 12 px
  /// short under the stress pack, where `density.chip` is 12 px vertical
  /// against ink's 6). Note the failure mode is invisible to the M14 log gate:
  /// an under-reserved AppBar bottom clips, it does not throw.
  group('T-0263 · the header-height derivation matches a real chip', () {
    for (final scale in [1.0, 1.3]) {
      testWidgets('textScaler $scale', (tester) async {
        await tester.pumpWidget(
          Builder(
            builder: (_) {
              late ThemeData theme;
              runZonedGuarded(
                () => theme = FuzzzyLawTheme.dark(),
                (e, _) {
                  if (!isFontLoaderNoise(e)) unexpectedZoneErrors.add(e);
                },
              );
              return MaterialApp(
                theme: theme,
                home: MediaQuery(
                  data: MediaQueryData(textScaler: TextScaler.linear(scale)),
                  child: const Scaffold(
                    body: Center(
                      child: AppDomainChip(
                        domain: domain,
                        parent: AppChipParent.ground,
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
        );

        final ctx = tester.element(find.byType(AppDomainChip));
        final probe = TextPainter(
          text: TextSpan(text: 'ა', style: ctx.fuzzzyTextStyles.control),
          textDirection: TextDirection.ltr,
          textScaler: MediaQuery.textScalerOf(ctx),
          maxLines: 1,
        )..layout();

        expect(
          probe.height + ctx.fuzzzyDensity.chip.vertical + 2,
          tester.getSize(find.byType(AppDomainChip)).height,
          reason:
              'the reserve `_headerHeight` computes must equal the height the '
              'chip actually takes — otherwise the AppBar bottom clips, and '
              'clipping does not raise a layout error',
        );
      });
    }
  });
}
