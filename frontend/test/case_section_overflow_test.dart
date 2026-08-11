import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:themasteroflaw/src/src.dart';

/// Phase M · Unit A · **M14d — the T-0255 regression lock, and the M14 matrix
/// pulled down to a widget test.**
///
/// `T-0255`: the argument card's header `Row` overflowed by **2.9 px on the
/// right at `textScaler` 1.3 / 360 dp, in both skins**, because the title
/// `Text` and the `AppStatusChip` were neither `Flexible` nor `Expanded` and
/// both took their natural width — the unbounded-growth mode
/// `PHASE_M_CONTRACT` §3.1.13 predicts for this app (`maxLines` / `overflow` /
/// `ellipsis` appear **zero** times across the files in scope).
///
/// 🔴 **Why this file exists rather than "we re-ran the device cell".** The
/// device matrix costs ~90 s per cell, needs an emulator, a seeded Hive case
/// and a pty-wrapped `flutter run` (see JOURNAL M14 §C — three of the four
/// obvious log sources are blind and produce false greens). None of that
/// survives into CI. A `RenderFlex overflowed` is an ordinary framework
/// exception in a widget test, so the **same** defect is catchable here, on
/// every `flutter test`, for free — provided the test actually pins the two
/// axes that make it fire: the **viewport width** and the **textScaler**.
///
/// So each section is pumped at all six (textScaler × width) points of the
/// M14 matrix — 1.0 · 1.3 × 360 · 599 · 601 dp — with the **real longest
/// Georgian strings from contract §3.1.14** (121/113/107/106/103/102 chars),
/// never lorem. The skin axis is covered separately: skins change colour, not
/// metrics, and `theme_roles_test` already asserts both skins resolve.
///
/// 🔴 **This is a PROXY for the device matrix, not a replica, and the reason
/// is the font.** `flutter test` runs the tester with `--use-test-fonts
/// --disable-asset-fonts`, so every glyph here is the fixed-advance test font,
/// **not** Noto Sans Georgian. The pixel counts therefore do not match the
/// device's: the header row that overflowed by **2.9 px** on the emulator
/// overflows by **111 px** here, and it fires at textScaler 1.0 as well as
/// 1.3. That makes this test *stricter* than the device and its numbers
/// meaningless — so **never quote a pixel count from here as a device
/// finding**, and never treat a green here as the M14 gate. The device matrix
/// (M14e/M14b) remains the authority for the real typeface.
///
/// Being font-independent is the point, not a flaw: `T-0252` says the app
/// **fetches** its fonts over HTTP rather than bundling them, so a cold or
/// offline device renders Georgian in a *platform fallback* at metrics nobody
/// certified. A row that only fits in one specific typeface is broken there.
/// A row that survives this test survives that.
///
/// **Seen to fail** before the fix, in five of the 48 cells, and it named four
/// distinct sites — one more than the ticket knew about and three more than
/// the device run found:
///
/// | site | fired at |
/// |---|---|
/// | `case_arguments_section.dart:380` (T-0255, the card header) | 1.0 · 360 and 1.3 · 360 |
/// | `case_arguments_section.dart:445` (the AI-provenance row) | 1.0 · 360 and 1.3 · 360 |
/// | `case_overview_section.dart:413` (the action-plan heading) | 1.3 · 360 |
/// | `case_risks_section.dart:166` (the AI-provenance row) | 1.0 · 360 and 1.3 · 360 |
///
/// All four are one bug class — an unwrapped `Text` sharing a `Row` with a
/// non-scaling icon or a chip — and all four are fixed with the app's own
/// existing idiom (`Expanded`, as `case_risks_section`'s mitigation row and
/// `case_card`'s title row already did). A lock never seen red is not a lock
/// (same discipline as M13 §A and M13b §C).
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  // See theme_roles_test.dart: narrowing, not weakening — a test must not
  // depend on an HTTP font fetch (which is also T-0252's subject).
  GoogleFonts.config.allowRuntimeFetching = false;

  final unexpectedZoneErrors = <Object>[];
  bool isFontLoaderNoise(Object e) {
    final s = e.toString();
    return s.contains('allowRuntimeFetching') ||
        s.contains('Failed to load font');
  }

  setUp(unexpectedZoneErrors.clear);
  tearDown(() => expect(unexpectedZoneErrors, isEmpty));

  // ── contract §3.1.14, the longest strings the app can actually hold ──────
  const g121 =
      'სასამართლოს მიერ მიღებული გადაწყვეტილება, რომელიც მომავალში ანალოგიური '
      'საქმეების განხილვისას სახელმძღვანელოდ გამოიყენება.';
  const g113 =
      'ვალდებულების შესრულების უზრუნველყოფის საშუალება, როდესაც პირი კისრულობს '
      'პასუხისმგებლობას სხვისი ვალდებულებისთვის.';
  const g107 =
      'ფაქტის ან მდგომარეობის არსებობის ვარაუდი, სანამ საპირისპირო არ დამტკიცდება '
      '(მაგ. უდანაშაულობის პრეზუმფცია).';
  const g106 =
      'სააპელაციო სასამართლოს გადაწყვეტილების გასაჩივრება უზენაეს სასამართლოში '
      'სამართლის ნორმების დარღვევის გამო.';
  const g103 =
      'იძულებითი ზომა, რომელიც გამოიყენება სამართალდარღვევის ჩადენისათვის '
      '(მაგ. ჯარიმა, თავისუფლების აღკვეთა).';
  // The split falls inside the hyphenated compound `უფლება-მოვალეობების`, so
  // the lint's suggested space would silently change the contract string into
  // one the app can never hold. The string wins; the lint is pinned here with
  // its reason rather than obeyed.
  const g102 =
      // ignore: missing_whitespace_between_adjacent_strings
      'გარდაცვლილი პირის ქონებრივი და ზოგიერთი პირადი არაქონებრივი უფლება-'
      'მოვალეობების გადასვლა სხვა პირებზე.';

  final now = DateTime(2026, 8, 11);

  CaseData buildCase() => CaseData(
    id: 'qa-case',
    title: 'ქურდობის ბრალდება — QA ტესტი',
    domainIndex: LegalDomain.criminal.index,
    createdAt: now,
    updatedAt: now,
    facts: [
      FactData(
        id: 'f1',
        text: g121,
        classificationIndex: FactClassification.favorable.index,
        createdAt: now,
      ),
      FactData(
        id: 'f2',
        text: g113,
        classificationIndex: FactClassification.unfavorable.index,
        createdAt: now,
      ),
    ],
    arguments: [
      ArgumentData(
        id: 'a1',
        title: g106,
        explanation: g121,
        // `weak` is the widest Georgian strength label's neighbour; every
        // rung is exercised by the three arguments below.
        strengthIndex: ArgumentStrength.moderate.index,
        linkedArticleIds: ['art-1'],
        isAiGenerated: true,
        createdAt: now,
      ),
      ArgumentData(
        id: 'a2',
        title: g113,
        explanation: g107,
        strengthIndex: ArgumentStrength.strong.index,
        createdAt: now,
      ),
      ArgumentData(
        id: 'a3',
        title: g103,
        explanation: g102,
        strengthIndex: ArgumentStrength.weak.index,
        createdAt: now,
      ),
    ],
    evidence: [
      EvidenceData(
        id: 'e1',
        title: g107,
        typeIndex: EvidenceType.document.index,
        addedAt: now,
      ),
    ],
    strategy: StrategyData(
      primaryStrategy: g121,
      backupStrategy: g113,
      fallbackPosition: g107,
      confidenceScore: 62,
    ),
    timeline: [
      TimelineEventData(
        id: 't1',
        date: now,
        title: g102,
        description: g103,
        typeIndex: 0,
      ),
    ],
    risks: [
      RiskData(
        id: 'r1',
        description: g107,
        severityIndex: 1,
        mitigationSuggestion: g103,
        isAiGenerated: true,
      ),
    ],
    actionItems: [
      ActionItemData(id: 'i1', task: g103, priorityIndex: 0, deadline: now),
      ActionItemData(
        id: 'i2',
        task: g102,
        priorityIndex: 1,
        isCompleted: true,
      ),
    ],
    linkedArticles: [
      LinkedArticleData(
        articleId: 'art-1',
        title: g106,
        codeName: 'სისხლის სამართლის კოდექსი',
        snippet: g113,
        savedAt: now,
        url: 'https://matsne.gov.ge/ka/document/view/16426',
      ),
    ],
  );

  /// Pump [child] at an exact logical viewport and textScaler.
  ///
  /// 🔴 `tester.view.physicalSize` + `devicePixelRatio: 1` is the widget-test
  /// equivalent of the device recipe `wm density 160; wm size <W>x800` from
  /// JOURNAL M14 §F — 1 dp = 1 px, so the width in the cell name is the width
  /// the layout actually gets. Without pinning it, every test runs at Flutter's
  /// default 800×600 and the 360 dp cell — the ONLY cell T-0255 fired in —
  /// would never be exercised.
  ///
  /// Returns every layout error the frame produced, **not just the first**.
  /// `tester.takeException()` yields one exception per pump, so a row that
  /// overflows three times in one list reads as a single defect and the other
  /// two are invisible until the first is fixed. Capturing `FlutterError.
  /// onError` collects all of them, with the error-causing widget's own source
  /// location in the message — which is what makes a failure here actionable
  /// without re-running anything.
  Future<List<String>> pumpAt(
    WidgetTester tester,
    Widget child, {
    required double width,
    required double scale,
  }) async {
    final layoutErrors = <String>[];
    final previousOnError = FlutterError.onError;
    FlutterError.onError = (details) {
      // 🔴 `details.toString()` does NOT carry the error-causing widget's
      // source location. That location is produced by
      // `debugTransformDebugCreator`, which `FlutterErrorDetails` runs only
      // when it is rendered as a diagnostics node
      // (`assertions.dart:1298-1325`, SDK 3.32.0). So go through
      // `toDiagnosticsNode()`, or every failure reports a pixel count with no
      // address and the next reader has to re-run the whole matrix by hand.
      final info = details.toDiagnosticsNode().toStringDeep();
      final where = RegExp(
        r'lib/src/[^\s:]+\.dart:\d+:\d+',
      ).firstMatch(info)?.group(0);
      layoutErrors.add(
        '${details.exception}'
        '${where == null ? '' : '  ← $where'}',
      );
      // 🔴 CHAIN, never replace. `flutter_test`'s own handler is what
      // completes the test's error pipeline; swallowing it deadlocks the run
      // (seen: the first version of this file hung `flutter test` for 10
      // minutes with no output). The binding still records the first
      // exception, which the caller drains with `takeException()`.
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
      MaterialApp(
        theme: theme,
        home: MediaQuery(
          data: MediaQueryData(
            size: Size(width, 800),
            textScaler: TextScaler.linear(scale),
          ),
          child: Scaffold(body: child),
        ),
      ),
    );
    await tester.pump(const Duration(milliseconds: 300));
    return layoutErrors;
  }

  /// The six (textScaler × width) points of the M14 matrix.
  const cells = <(double, double)>[
    (1.0, 360),
    (1.0, 599),
    (1.0, 601),
    (1.3, 360), // ← the cell T-0255 fired in, and only this one
    (1.3, 599),
    (1.3, 601),
  ];

  /// Every case-workspace section that can be pumped without a Cubit in
  /// `build` (the other two — chat and tasks — read one during build and are
  /// device-only; they are covered by the M14e device matrix, not here).
  final sections = <String, Widget Function(CaseData)>{
    'overview': (c) => CaseOverviewSection(caseData: c, onTabSwitch: (_) {}),
    'facts': (c) => CaseFactsSection(caseData: c),
    'arguments': (c) => CaseArgumentsSection(caseData: c),
    'evidence': (c) => CaseEvidenceSection(caseData: c),
    'strategy': (c) => CaseStrategySection(caseData: c),
    'timeline': (c) => CaseTimelineSection(caseData: c),
    'risks': (c) => CaseRisksSection(caseData: c),
    'laws': (c) => CaseLawsSection(caseData: c),
  };

  for (final entry in sections.entries) {
    group('${entry.key} section lays out without overflow', () {
      for (final (scale, width) in cells) {
        testWidgets('textScaler $scale · ${width.toInt()} dp', (tester) async {
          final errors = await pumpAt(
            tester,
            entry.value(buildCase()),
            width: width,
            scale: scale,
          );
          // Drain the binding's pending exception: `errors` is the richer
          // report and is what this test asserts on.
          tester.takeException();
          expect(
            errors,
            isEmpty,
            reason:
                'M14 gate: no RenderFlex overflow / layout assertion is '
                'allowed in any matrix cell (plan §4 lists it as a defect, '
                'never an expected change).\n  ${errors.join('\n  ')}',
          );
        });
      }
    });
  }
}
