import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:themasteroflaw/src/src.dart';

/// The three rungs of risk severity, as roles.
///
/// Same shape as `case_arguments_section._strengthRole` and M8's
/// `_classificationRole`. MAPPING §2.6 pre-mapped `RiskSeverity.high →
/// destructive` and §2.1 mapped all four `infoColor` switch arms (of which
/// `RiskSeverity.low` is one) to `info` at M0; this executes that.
///
/// The role appears only as the card's **4px leading rule** or the chip's own
/// **border and 8px dot** — never as a fill (M7/M8's red discipline).
Color _severityRole(FuzzzyColors c, RiskSeverity s) => switch (s) {
  RiskSeverity.high => c.destructive,
  RiskSeverity.medium => c.warning,
  RiskSeverity.low => c.info,
};

/// Risks + weaknesses: severity badges, mitigation, "Red Team" button.
class CaseRisksSection extends StatelessWidget {
  const CaseRisksSection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return Column(
      children: [
        Expanded(
          child: caseData.risks.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Dimension: the oversized empty-state glyph, on M4's
                      // `inkFaint` like every other 48/64px state glyph here.
                      // An EMPTY risk list is not a warning — the fork's amber
                      // said the opposite of what the copy below says.
                      Icon(
                        Icons.warning_amber,
                        size: 48,
                        color: colors.inkFaint,
                      ),
                      SizedBox(height: space.l),
                      Text(
                        'რისკები ჯერ არ არის',
                        style: type.body.copyWith(color: colors.inkMute),
                      ),
                      SizedBox(height: space.s),
                      Text(
                        'სუსტი მხარეების გამოვლენა\nგეხმარებათ უკეთეს მომზადებაში',
                        style: type.bodyS.copyWith(color: colors.inkMute),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                )
              : ListView.separated(
                  padding: density.screen,
                  itemCount: caseData.risks.length,
                  separatorBuilder: (_, __) => SizedBox(height: space.s),
                  itemBuilder: (context, index) {
                    final risk = caseData.risks[index];
                    final severityRole = _severityRole(colors, risk.severity);
                    return Dismissible(
                      key: ValueKey(risk.id),
                      direction: DismissDirection.endToStart,
                      onDismissed: (_) =>
                          context.read<CaseDetailCubit>().deleteRisk(risk.id),
                      background: Container(
                        alignment: Alignment.centerRight,
                        padding: EdgeInsets.only(right: space.l),
                        // Duty 4's IDLE form — a `destructiveText` glyph on no
                        // fill. Deliberately NOT the filled red reveal M7/M8
                        // gave the case and fact swipes: this screen already
                        // spends `destructive` on `RiskSeverity.high`, and a
                        // filled reveal behind a card that carries a red rule
                        // would put two red weights in one gesture.
                        child: Icon(
                          Icons.delete,
                          color: colors.destructiveText,
                        ),
                      ),
                      child: Container(
                        padding: density.panel,
                        decoration: BoxDecoration(
                          color: colors.surface,
                          borderRadius: BorderRadius.circular(radius.m),
                          // The severity keeps its 4px leading rule — the
                          // sanctioned home for a semantic colour — and the
                          // other three sides GAIN the `line` hairline the
                          // fork never drew. Same shape as `FuzzzyCard(
                          // leadingRule:)` and M7's CaseCard.
                          border: Border(
                            left: BorderSide(color: severityRole, width: 4),
                            top: BorderSide(color: colors.line),
                            right: BorderSide(color: colors.line),
                            bottom: BorderSide(color: colors.line),
                          ),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    risk.description,
                                    style: type.titleS.copyWith(
                                      color: colors.ink,
                                    ),
                                  ),
                                ),
                                _SeverityChip(severity: risk.severity),
                              ],
                            ),
                            if (risk.mitigationSuggestion != null &&
                                risk.mitigationSuggestion!.isNotEmpty) ...[
                              SizedBox(height: space.s),
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  // An inline leading glyph takes the SAME rung
                                  // as the text it leads (the rule M8's
                                  // provenance row set). A mitigation note is
                                  // supplementary to the risk above it, so both
                                  // are `inkMute`; the fork's gold icon made
                                  // the suggestion louder than the risk.
                                  Icon(
                                    Icons.lightbulb_outline,
                                    size: 16,
                                    color: colors.inkMute,
                                  ),
                                  SizedBox(width: space.xs),
                                  Expanded(
                                    child: Text(
                                      risk.mitigationSuggestion!,
                                      style: type.body.copyWith(
                                        color: colors.inkMute,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                            if (risk.isAiGenerated) ...[
                              SizedBox(height: space.xs),
                              Row(
                                children: [
                                  // Provenance is META (USING §2.2) → inkFaint.
                                  Icon(
                                    Icons.psychology,
                                    size: 14,
                                    color: colors.inkFaint,
                                  ),
                                  SizedBox(width: space.xs),
                                  Text(
                                    'AI-ის მიერ გენერირებული',
                                    style: type.bodyS.copyWith(
                                      color: colors.inkFaint,
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ],
                        ),
                      ),
                    );
                  },
                ),
        ),
        Padding(
          padding: density.screen,
          child: SizedBox(
            width: double.infinity,
            // Dimension: the full-width CTA height (M8's add-fact button).
            height: 48,
            child: OutlinedButton.icon(
              onPressed: () => _showAddRisk(context),
              icon: const Icon(Icons.add),
              label: const Text('რისკის დამატება'),
              // `FuzzzyButton.secondary`'s shape: `ink` label, `lineStrong`
              // side (M8 judgement 9).
              style: OutlinedButton.styleFrom(
                foregroundColor: colors.ink,
                side: BorderSide(color: colors.lineStrong),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(radius.m),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  void _showAddRisk(BuildContext parentContext) {
    final descController = TextEditingController();
    final mitigationController = TextEditingController();
    var severity = RiskSeverity.medium;

    showModalBottomSheet<void>(
      context: parentContext,
      isScrollControlled: true,
      // The sheet draws its own `raised` + `lineStrong` box (M5's
      // feedback_sheet idiom), so the route must not paint a second one.
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        final colors = ctx.fuzzzyColors;
        final type = ctx.fuzzzyTextStyles;
        final space = ctx.fuzzzySpace;
        final radius = ctx.fuzzzyRadius;
        final density = ctx.fuzzzyDensity;

        return StatefulBuilder(
          builder: (ctx, setState) => Container(
            decoration: BoxDecoration(
              color: colors.raised,
              border: Border(top: BorderSide(color: colors.lineStrong)),
              borderRadius: BorderRadius.vertical(
                top: Radius.circular(radius.l),
              ),
            ),
            padding: density.dialog.copyWith(
              bottom:
                  density.dialog.bottom + MediaQuery.of(ctx).viewInsets.bottom,
            ),
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'ახალი რისკი',
                    style: type.titleM.copyWith(color: colors.ink),
                  ),
                  SizedBox(height: space.l),
                  TextField(
                    controller: descController,
                    maxLines: 3,
                    style: type.body.copyWith(color: colors.fieldText),
                    // Everything about the box comes from M1's
                    // inputDecorationTheme (RUN_BRIEF §4).
                    decoration: const InputDecoration(
                      hintText: 'აღწერეთ რისკი...',
                    ),
                  ),
                  SizedBox(height: space.m),
                  Text(
                    'სიმძიმე:',
                    // A Georgian section label above an input is `control`
                    // (JOURNAL M6 §G).
                    style: type.control.copyWith(color: colors.inkMute),
                  ),
                  SizedBox(height: space.s),
                  Row(
                    children: RiskSeverity.values.map((s) {
                      final isSelected = s == severity;
                      final role = _severityRole(colors, s);
                      return Expanded(
                        child: GestureDetector(
                          behavior: HitTestBehavior.opaque,
                          onTap: () => setState(() => severity = s),
                          child: Container(
                            padding: density.tile,
                            margin: EdgeInsets.symmetric(horizontal: space.xs),
                            // `FuzzzySegmentedControl`'s law: a discrete choice
                            // takes its fill from the ACTION PAIR, never from
                            // the severity — the fork put a red fill on "high"
                            // when it was selected, banned by USING §6. The
                            // severity rides the 8px dot in both states.
                            decoration: BoxDecoration(
                              color: isSelected
                                  ? colors.actionPrimaryBg
                                  : colors.surface,
                              borderRadius: BorderRadius.circular(radius.s),
                              border: Border.all(
                                color: isSelected
                                    ? colors.actionPrimaryBg
                                    : colors.line,
                              ),
                            ),
                            child: Column(
                              children: [
                                Container(
                                  // §4.4's one status-dot diameter.
                                  width: 8,
                                  height: 8,
                                  decoration: BoxDecoration(
                                    color: role,
                                    borderRadius: BorderRadius.circular(
                                      radius.circle,
                                    ),
                                  ),
                                ),
                                SizedBox(height: space.xs),
                                Text(
                                  s.displayNameKa,
                                  textAlign: TextAlign.center,
                                  style: type.control.copyWith(
                                    color: isSelected
                                        ? colors.actionPrimaryFg
                                        : colors.inkMute,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                  SizedBox(height: space.m),
                  TextField(
                    controller: mitigationController,
                    maxLines: 2,
                    style: type.body.copyWith(color: colors.fieldText),
                    decoration: const InputDecoration(
                      hintText: 'შემარბილებელი ზომა (არასავალდებულო)...',
                    ),
                  ),
                  SizedBox(height: space.l),
                  SizedBox(
                    width: double.infinity,
                    // Dimension: the sheet's commit CTA.
                    height: 48,
                    child: ElevatedButton(
                      onPressed: () {
                        if (descController.text.trim().isEmpty) return;
                        parentContext.read<CaseDetailCubit>().addRisk(
                          RiskData(
                            id: DateTime.now().millisecondsSinceEpoch
                                .toString(),
                            description: descController.text.trim(),
                            severityIndex: severity.index,
                            mitigationSuggestion:
                                mitigationController.text.trim().isEmpty
                                ? null
                                : mitigationController.text.trim(),
                          ),
                        );
                        Navigator.pop(ctx);
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: colors.actionPrimaryBg,
                        foregroundColor: colors.actionPrimaryFg,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(radius.m),
                        ),
                      ),
                      // A button label is `control`, always.
                      child: Text('დამატება', style: type.control),
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      },
    );
  }
}

/// The severity marker on a risk card — `FuzzzyStatusChip`'s recipe, app-side.
///
/// Third instance of the same app-side twin (`_TrustBadge` M8b §C,
/// `_StrengthChip` M9), all for the same reason: the kit chip labels in
/// `fuzzzyTextStyles.label`, the uppercase **mono, Latin-only** eyebrow role,
/// and `displayNameKa` is Georgian. M11 consolidates all three.
///
/// No fill, a 1px `Color.lerp(ground, role, 0.40)` border, `density.chip`,
/// `radius.s`, an 8px leading disc, label in the role. The fork's `alpha 0.15`
/// fill is deleted — a red-filled "high" badge is exactly what USING §6 bans.
class _SeverityChip extends StatelessWidget {
  const _SeverityChip({required this.severity});
  final RiskSeverity severity;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final role = _severityRole(colors, severity);

    return Container(
      padding: density.chip,
      decoration: BoxDecoration(
        border: Border.all(color: Color.lerp(colors.ground, role, 0.40)!),
        borderRadius: BorderRadius.circular(radius.s),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            // Dimension: §4.4's one status-dot diameter.
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              color: role,
              borderRadius: BorderRadius.circular(radius.circle),
            ),
          ),
          SizedBox(width: space.s),
          Text(
            severity.displayNameKa,
            style: type.control.copyWith(color: role),
          ),
        ],
      ),
    );
  }
}
