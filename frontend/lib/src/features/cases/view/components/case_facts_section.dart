import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

/// Facts management with three-segment categorization: Favorable/Unfavorable/Neutral.
class CaseFactsSection extends StatefulWidget {
  const CaseFactsSection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  State<CaseFactsSection> createState() => _CaseFactsSectionState();
}

/// The classification taxonomy's semantic role. Unlike the legal-DOMAIN
/// palette (which is app-supplied — see `LegalDomainColors`), these three
/// genuinely are kit semantics: a favourable fact helps the case, an
/// unfavourable one hurts it, a neutral one is information.
///
/// It appears on screen only as a 4px leading rule or an 8px dot — never as
/// text, never as a fill. Selection is carried by the action pair instead
/// (USING §6: *"a discrete choice takes a fill from the action pair — never
/// red"*).
Color _classificationRole(FuzzzyColors c, FactClassification fc) =>
    switch (fc) {
      FactClassification.favorable => c.success,
      FactClassification.unfavorable => c.destructive,
      FactClassification.neutral => c.info,
    };

class _CaseFactsSectionState extends State<CaseFactsSection> {
  late FactClassification _selectedFilter = _initialFilter();

  FactClassification _initialFilter() {
    for (final fc in FactClassification.values) {
      if (widget.caseData.facts.any((f) => f.classificationIndex == fc.index)) {
        return fc;
      }
    }
    return FactClassification.favorable;
  }

  List<FactData> get _filteredFacts => widget.caseData.facts
      .where((f) => f.classificationIndex == _selectedFilter.index)
      .toList();

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final motion = context.fuzzzyMotion;

    return Column(
      children: [
        // Segment control
        Padding(
          padding: density.screen,
          child: Row(
            children: FactClassification.values.map((fc) {
              final count = widget.caseData.facts
                  .where((f) => f.classificationIndex == fc.index)
                  .length;
              final isSelected = fc == _selectedFilter;
              final role = _classificationRole(colors, fc);
              return Expanded(
                child: GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: () => setState(() => _selectedFilter = fc),
                  child: AnimatedContainer(
                    duration: motion.fast,
                    curve: motion.fastCurve,
                    padding: density.tile,
                    decoration: BoxDecoration(
                      // `FuzzzySegmentedControl`'s law (RUN_DECISIONS §2): a
                      // discrete choice takes a fill from the ACTION PAIR. The
                      // fork tinted the selected segment with the
                      // classification's own colour, which put a red fill on
                      // "unfavourable" — banned outright by USING §6.
                      color: isSelected
                          ? colors.actionPrimaryBg
                          : colors.surface,
                      borderRadius: BorderRadius.circular(radius.s),
                      // Border reserved at a CONSTANT width in both states —
                      // the fork's unselected border was `Colors.transparent`,
                      // which is fine, but the width must never change.
                      border: Border.all(
                        color: isSelected
                            ? colors.actionPrimaryBg
                            : colors.line,
                      ),
                    ),
                    child: Column(
                      children: [
                        Container(
                          // §4.4's one status-dot diameter. Replaces the fork's
                          // ✅/❌/ℹ️ emoji at a hardcoded fontSize: 18 — the dot
                          // is what the emoji stood for, and it re-skins.
                          width: 8,
                          height: 8,
                          decoration: BoxDecoration(
                            color: role,
                            borderRadius: BorderRadius.circular(radius.circle),
                          ),
                        ),
                        SizedBox(height: space.xs),
                        // 🔴 BOUNDED at M20b. This `Column` sits above an
                        // `Expanded` facts list, so whatever height it takes is
                        // taken FROM that list — and with three tiles sharing
                        // 360 dp there is only ~60 dp of inner width per label.
                        // Under the stress pack at `textScaler` 1.3 a word like
                        // `ხელსაყრელი` wrapped to five ~3-glyph lines, the
                        // control grew to ~230 px, the `Expanded` was handed
                        // negative space and the section overflowed by 3.5 px
                        // (found by the M20 device re-run, cell
                        // `m20-stress-night-1.3-360`, 6 gate hits).
                        //
                        // `maxLines` bounds it deterministically — and the
                        // BOUND IS MEASURED, not picked. The shipped ink pack
                        // needs exactly **three** lines at `textScaler` 1.3
                        // (`ხელსაყ / რელი / (2)`), so 3 is the smallest value
                        // that is a genuine no-op there.
                        //
                        // 🔴 `maxLines: 2` was tried first and REJECTED on
                        // device evidence: it cut ink at 1.3 to
                        // `ხელსაყ / რელი (…`, i.e. it fixed the stress pack by
                        // truncating the SHIPPED one — trading a defect the
                        // gate can see for one it cannot, which is the whole
                        // failure mode `T-0264` is about. Compare
                        // `harness/shots/m20-ink-night-1.3-360/step27_0.png`
                        // (3 lines, full) against the 2-line attempt.
                        //
                        // Under the stress pack 3 lines still bounds the
                        // control well below the height that overflowed, so the
                        // trade is paid only by the deliberately-hostile probe
                        // pack — and a `RenderFlex` overflow is a plan §4
                        // defect while the stress pack is not a shipping
                        // configuration.
                        //
                        // NOT the whole answer: a 3-up segmented control that
                        // cannot fit its labels wants to scroll or stack, not
                        // ellipse. That is a redesign with no product mandate,
                        // so it is recorded in `T-0264` rather than done here.
                        Text(
                          '${fc.displayNameKa} ($count)',
                          style: type.control.copyWith(
                            color: isSelected
                                ? colors.actionPrimaryFg
                                : colors.inkMute,
                          ),
                          textAlign: TextAlign.center,
                          maxLines: 3,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ),

        // Facts list
        Expanded(
          child: _filteredFacts.isEmpty
              ? Center(
                  child: Text(
                    'ჯერ არ არის ${_selectedFilter.displayNameKa} ფაქტი',
                    style: type.body.copyWith(color: colors.inkMute),
                  ),
                )
              : ListView.separated(
                  padding: EdgeInsets.symmetric(
                    horizontal: density.screen.left,
                  ),
                  itemCount: _filteredFacts.length,
                  separatorBuilder: (_, __) => SizedBox(height: space.s),
                  itemBuilder: (context, index) {
                    final fact = _filteredFacts[index];
                    final role = _classificationRole(
                      colors,
                      fact.classification,
                    );
                    return Dismissible(
                      key: ValueKey(fact.id),
                      direction: DismissDirection.endToStart,
                      onDismissed: (_) =>
                          context.read<CaseDetailCubit>().deleteFact(fact.id),
                      background: Container(
                        alignment: Alignment.centerRight,
                        padding: EdgeInsets.only(right: space.l),
                        decoration: BoxDecoration(
                          // A swipe-to-delete reveal IS the destructive commit
                          // in flight — duty 4's one sanctioned red fill. It is
                          // the same red VOICE as the "unfavourable" rule
                          // below, not a second one, so §6's rule holds.
                          color: colors.destructive,
                          borderRadius: BorderRadius.circular(radius.m),
                        ),
                        child: Icon(Icons.delete, color: colors.onRed),
                      ),
                      // `FuzzzyCard(leadingRule:)`: the classification's role is
                      // the 4px rule, and the card gains the `line` hairline the
                      // fork never drew. T-0254: a per-side `Border` +
                      // `borderRadius` throws at paint — `AppRuleCard` carries
                      // the kit's real (uniform border + clipped overlay) idiom.
                      child: AppRuleCard(
                        rule: role,
                        borderRadius: radius.m,
                        padding: density.panel,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              fact.text,
                              style: type.body.copyWith(color: colors.ink),
                            ),
                            if (fact.isAiGenerated) ...[
                              SizedBox(height: space.xs),
                              Row(
                                children: [
                                  // Provenance is META (USING §2.2), so it is
                                  // `inkFaint` — the fork's gold made an
                                  // attribution line louder than the fact.
                                  Icon(
                                    Icons.psychology,
                                    size: 14,
                                    color: colors.inkFaint,
                                  ),
                                  SizedBox(width: space.xs),
                                  Text(
                                    'AI-ით ამოცნობილი',
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

        // Add fact button
        Padding(
          padding: density.screen,
          child: SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => _showAddFactDialog(context),
              icon: const Icon(Icons.add),
              label: const Text('დაამატეთ ფაქტი'),
              // `FuzzzyButton.secondary`: `ink` label on a `lineStrong`
              // outline. The fork's gold-at-alpha-0.3 border is exactly the
              // "tinted border" row MAPPING §2.2 sends to a line role.
              style: OutlinedButton.styleFrom(
                foregroundColor: colors.ink,
                side: BorderSide(color: colors.lineStrong),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(radius.m),
                ),
                padding: density.snug,
                textStyle: type.control,
              ),
            ),
          ),
        ),
      ],
    );
  }

  void _showAddFactDialog(BuildContext context) {
    final controller = TextEditingController();
    var classification = _selectedFilter;

    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      // The sheet draws its own `raised` + `lineStrong` box (M5's idiom), so
      // the route must not paint a second one under it.
      backgroundColor: Colors.transparent,
      builder: (sheetContext) {
        return StatefulBuilder(
          builder: (ctx, setSheetState) {
            final colors = ctx.fuzzzyColors;
            final type = ctx.fuzzzyTextStyles;
            final space = ctx.fuzzzySpace;
            final radius = ctx.fuzzzyRadius;
            final density = ctx.fuzzzyDensity;
            return Container(
              decoration: BoxDecoration(
                color: colors.raised,
                border: Border(top: BorderSide(color: colors.lineStrong)),
                borderRadius: BorderRadius.vertical(
                  top: Radius.circular(radius.l),
                ),
              ),
              padding: density.dialog.copyWith(
                bottom:
                    density.dialog.bottom +
                    MediaQuery.of(ctx).viewInsets.bottom,
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'ახალი ფაქტი',
                    style: type.titleM.copyWith(color: colors.ink),
                  ),
                  SizedBox(height: space.l),
                  TextField(
                    controller: controller,
                    maxLines: 3,
                    style: type.body.copyWith(color: colors.fieldText),
                    // Box + hint style come from M1's inputDecorationTheme.
                    decoration: const InputDecoration(
                      hintText: 'აღწერეთ ფაქტი...',
                    ),
                  ),
                  SizedBox(height: space.l),
                  Row(
                    children: FactClassification.values.map((fc) {
                      final isSelected = fc == classification;
                      final role = _classificationRole(colors, fc);
                      return Expanded(
                        child: GestureDetector(
                          behavior: HitTestBehavior.opaque,
                          onTap: () => setSheetState(() => classification = fc),
                          child: Container(
                            padding: density.chip,
                            margin: EdgeInsets.symmetric(horizontal: space.xs),
                            decoration: BoxDecoration(
                              // Parent is the sheet's `raised` rung → the
                              // resting chip steps down to `surface`.
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
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Container(
                                  width: 8,
                                  height: 8,
                                  decoration: BoxDecoration(
                                    color: role,
                                    borderRadius: BorderRadius.circular(
                                      radius.circle,
                                    ),
                                  ),
                                ),
                                SizedBox(width: space.xs),
                                Flexible(
                                  child: Text(
                                    fc.displayNameKa,
                                    textAlign: TextAlign.center,
                                    style: type.control.copyWith(
                                      color: isSelected
                                          ? colors.actionPrimaryFg
                                          : colors.inkMute,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      );
                    }).toList(),
                  ),
                  SizedBox(height: space.l),
                  SizedBox(
                    width: double.infinity,
                    // Dimension: the sheet's primary CTA height.
                    height: 48,
                    child: ElevatedButton(
                      onPressed: () {
                        if (controller.text.trim().isEmpty) return;
                        final fact = FactData(
                          id: DateTime.now().millisecondsSinceEpoch.toString(),
                          text: controller.text.trim(),
                          classificationIndex: classification.index,
                          createdAt: DateTime.now(),
                        );
                        context.read<CaseDetailCubit>().addFact(fact);
                        Navigator.pop(ctx);
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: colors.actionPrimaryBg,
                        foregroundColor: colors.actionPrimaryFg,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(radius.m),
                        ),
                      ),
                      child: Text('დამატება', style: type.control),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }
}
