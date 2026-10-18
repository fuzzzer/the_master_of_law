import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

/// Evidence management: grid/list of attached items with add button.
class CaseEvidenceSection extends StatelessWidget {
  const CaseEvidenceSection({super.key, required this.caseData});
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
          child: caseData.evidence.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      // Dimension: the oversized empty-state glyph, `inkFaint`.
                      Icon(Icons.attach_file, size: 48, color: colors.inkFaint),
                      SizedBox(height: space.l),
                      Text(
                        'ჯერ არ არის მტკიცებულება',
                        style: type.body.copyWith(color: colors.inkMute),
                      ),
                    ],
                  ),
                )
              : ListView.separated(
                  padding: density.screen,
                  itemCount: caseData.evidence.length,
                  separatorBuilder: (_, __) => SizedBox(height: space.s),
                  itemBuilder: (context, index) {
                    final ev = caseData.evidence[index];
                    final icon = switch (ev.type) {
                      EvidenceType.document => Icons.description,
                      EvidenceType.photo => Icons.photo,
                      EvidenceType.screenshot => Icons.screenshot,
                      EvidenceType.receipt => Icons.receipt,
                      EvidenceType.other => Icons.attachment,
                    };
                    return Container(
                      padding: density.tile,
                      decoration: BoxDecoration(
                        color: colors.surface,
                        borderRadius: BorderRadius.circular(radius.m),
                        // The tile GAINS the `line` hairline the fork never
                        // drew — on `ground` a bare `surface` box is nearly
                        // invisible in Ink.
                        border: Border.all(color: colors.line),
                      ),
                      child: Row(
                        children: [
                          // Dimension: the evidence-type glyph, the tile's
                          // leading identity mark. It leads the `ink` title, so
                          // it takes `ink` (M9 §E); the fork's gold made the
                          // attachment icon the loudest thing on the screen.
                          Icon(icon, color: colors.ink, size: 28),
                          SizedBox(width: space.m),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  ev.title,
                                  style: type.titleS.copyWith(
                                    color: colors.ink,
                                  ),
                                ),
                                Text(
                                  ev.type.displayNameKa,
                                  style: type.bodyS.copyWith(
                                    color: colors.inkMute,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          IconButton(
                            // Duty 4's idle form: a `destructiveText` glyph, no
                            // fill. `IconButton`'s own 48px constraint already
                            // clears the 44×44 minimum, so no FuzzzyHitTarget.
                            icon: Icon(
                              Icons.delete_outline,
                              color: colors.destructiveText,
                              size: 20,
                            ),
                            onPressed: () => context
                                .read<CaseDetailCubit>()
                                .deleteEvidence(ev.id),
                          ),
                        ],
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
              onPressed: () => _showAddEvidence(context),
              icon: const Icon(Icons.add),
              // M11b: the 📎 is DROPPED rather than re-iconified — this button
              // already has an icon slot, and "attach" plus "add" in the same
              // control is one signal drawn twice. `Icons.attach_file` carries
              // evidence on the tab and the overview stat card.
              label: const Text('დაამატეთ'),
              // `FuzzzyButton.secondary`'s shape (M8 judgement 9).
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

  void _showAddEvidence(BuildContext parentContext) {
    final cubit = parentContext.read<CaseDetailCubit>();
    final controller = TextEditingController();
    var selectedType = EvidenceType.document;

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
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'ახალი მტკიცებულება',
                  style: type.titleM.copyWith(color: colors.ink),
                ),
                SizedBox(height: space.l),
                TextField(
                  controller: controller,
                  style: type.body.copyWith(color: colors.fieldText),
                  // Everything about the box comes from M1's
                  // inputDecorationTheme (RUN_BRIEF §4).
                  decoration: const InputDecoration(hintText: 'სათაური...'),
                ),
                SizedBox(height: space.m),
                Wrap(
                  spacing: space.s,
                  runSpacing: space.s,
                  children: EvidenceType.values.map((t) {
                    final isSelected = t == selectedType;
                    // `FuzzzyFilterChip`'s exact recipe (inputs/
                    // fuzzzy_filter_chip.dart:92-112), the same one M5 gave the
                    // feedback categories: density.chip + radius.s, selection is
                    // INVERTED-MONO, never an accent tint (harvest/mol.md §4).
                    // `ChoiceChip` is dropped entirely — after M1 it would have
                    // fallen back to Material's own chipTheme (MAPPING §7).
                    return GestureDetector(
                      behavior: HitTestBehavior.opaque,
                      onTap: () => setState(() => selectedType = t),
                      child: Container(
                        padding: density.chip,
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
                        child: Text(
                          t.displayNameKa,
                          style: type.control.copyWith(
                            color: isSelected
                                ? colors.actionPrimaryFg
                                : colors.inkMute,
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
                SizedBox(height: space.l),
                SizedBox(
                  width: double.infinity,
                  // Dimension: the sheet's commit CTA.
                  height: 48,
                  child: ElevatedButton(
                    onPressed: () async {
                      if (controller.text.trim().isEmpty) return;
                      await cubit.addEvidence(
                        EvidenceData(
                          id: DateTime.now().millisecondsSinceEpoch.toString(),
                          title: controller.text.trim(),
                          typeIndex: selectedType.index,
                          addedAt: DateTime.now(),
                        ),
                      );
                      if (ctx.mounted) Navigator.pop(ctx);
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
        );
      },
    );
  }
}
