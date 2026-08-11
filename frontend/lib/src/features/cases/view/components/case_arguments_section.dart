import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:url_launcher/url_launcher.dart';

/// The three rungs of argument strength, as roles.
///
/// Same shape as `case_facts_section._classificationRole` (M8 §C): these
/// genuinely ARE kit semantics — a weak argument is a liability — which is
/// exactly why they are roles, and why the eight *legal-domain* colours next
/// door are not. MAPPING §2.6 pre-mapped `ArgumentStrength.weak → destructive`
/// at M0; this executes it rather than re-litigating it.
///
/// The screen has no other red voice (its delete affordance lives in the
/// workspace app bar, outlined, per M7), so the three-rung ramp survives here
/// where M8 §B had to demote the strength RING. The discipline that makes it
/// safe is unchanged: the role appears only as an **8px dot** or a chip's own
/// **border**, never as a fill.
Color _strengthRole(FuzzzyColors c, ArgumentStrength s) => switch (s) {
  ArgumentStrength.strong => c.success,
  ArgumentStrength.moderate => c.warning,
  ArgumentStrength.weak => c.destructive,
};

/// Arguments section with numbered cards, strength badges, and guided builder.
class CaseArgumentsSection extends StatelessWidget {
  const CaseArgumentsSection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    if (caseData.arguments.isEmpty) {
      return _EmptyArguments(onAdd: () => _showGuidedBuilder(context));
    }

    return Column(
      children: [
        Expanded(
          child: ListView.separated(
            padding: density.screen,
            itemCount: caseData.arguments.length,
            separatorBuilder: (_, __) => SizedBox(height: space.m),
            itemBuilder: (context, index) {
              final arg = caseData.arguments[index];
              return _ArgumentCard(
                index: index + 1,
                argument: arg,
                caseData: caseData,
                onDelete: () =>
                    context.read<CaseDetailCubit>().deleteArgument(arg.id),
              );
            },
          ),
        ),
        Padding(
          padding: density.screen,
          child: SizedBox(
            width: double.infinity,
            // Dimension: the full-width CTA height M8 set for the add-fact
            // button. Replaces the fork's `vertical: 14` padding — the wrong
            // axis for a button whose width is already forced.
            height: 48,
            child: OutlinedButton.icon(
              onPressed: () => _showGuidedBuilder(context),
              icon: const Icon(Icons.add),
              label: const Text('ახალი არგუმენტი'),
              // `FuzzzyButton.secondary`'s shape (M8 judgement 9): an `ink`
              // label on a `lineStrong` side. The fork's gold-at-alpha-0.3
              // border is the "tinted border" row MAPPING §2.2 sends to a
              // line role.
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

  void _showGuidedBuilder(BuildContext parentContext) {
    final whatController = TextEditingController();
    final whichLawController = TextEditingController();
    var strength = ArgumentStrength.moderate;

    showModalBottomSheet<void>(
      context: parentContext,
      isScrollControlled: true,
      // The sheet draws its OWN `raised` + `lineStrong` box and its own top
      // corners (M5's feedback_sheet idiom, adopted by new_case_sheet at M7),
      // so the route must not paint a second box under it — hence transparent
      // and no `shape:`. `Colors.transparent` is absence, not colour, and is
      // the one Material colour the guard sanctions.
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        final colors = ctx.fuzzzyColors;
        final type = ctx.fuzzzyTextStyles;
        final space = ctx.fuzzzySpace;
        final radius = ctx.fuzzzyRadius;
        final density = ctx.fuzzzyDensity;

        return StatefulBuilder(
          builder: (ctx, setSheetState) {
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
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'ახალი არგუმენტი',
                      style: type.titleM.copyWith(color: colors.ink),
                    ),
                    SizedBox(height: space.l),
                    // Step 1
                    Text(
                      'ნაბიჯი 1: რა მოხდა?',
                      // A Georgian section label above an input is `control` +
                      // `ink`, never `fieldLabel` (JOURNAL M6 §G). The fork's
                      // gold said "important"; Ink says it with the role.
                      style: type.control.copyWith(color: colors.ink),
                    ),
                    SizedBox(height: space.s),
                    TextField(
                      controller: whatController,
                      maxLines: 3,
                      style: type.body.copyWith(color: colors.fieldText),
                      // Fill, all five border states, radius, content padding
                      // and the hint style all come from M1's
                      // inputDecorationTheme (RUN_BRIEF §4).
                      decoration: const InputDecoration(
                        hintText: 'აღწერეთ სიტუაცია...',
                      ),
                    ),
                    SizedBox(height: space.l),
                    // Step 2
                    Text(
                      'ნაბიჯი 2: რომელი კანონი?',
                      style: type.control.copyWith(color: colors.ink),
                    ),
                    SizedBox(height: space.s),
                    TextField(
                      controller: whichLawController,
                      style: type.body.copyWith(color: colors.fieldText),
                      decoration: const InputDecoration(
                        hintText: 'მაგ: მუხ. 316 სამოქ. კოდ.',
                      ),
                    ),
                    SizedBox(height: space.l),
                    // Strength selector
                    Text(
                      'სიძლიერე:',
                      style: type.control.copyWith(color: colors.inkMute),
                    ),
                    SizedBox(height: space.s),
                    Row(
                      children: ArgumentStrength.values.map((s) {
                        final isSelected = s == strength;
                        final role = _strengthRole(colors, s);
                        return Expanded(
                          child: GestureDetector(
                            behavior: HitTestBehavior.opaque,
                            onTap: () => setSheetState(() => strength = s),
                            child: Container(
                              padding: density.tile,
                              margin: EdgeInsets.symmetric(
                                horizontal: space.xs,
                              ),
                              // `FuzzzySegmentedControl`'s law (RUN_DECISIONS
                              // §2), identical to the facts filter at M8 §C: a
                              // discrete choice takes its fill from the ACTION
                              // PAIR. The fork tinted the selected segment with
                              // the STRENGTH's own colour at alpha 0.2, which
                              // put a red fill on "weak" — banned outright by
                              // USING §6. The strength itself is carried by the
                              // 8px dot below, in both states.
                              decoration: BoxDecoration(
                                color: isSelected
                                    ? colors.actionPrimaryBg
                                    : colors.surface,
                                borderRadius: BorderRadius.circular(radius.s),
                                // Constant border width in both states — the
                                // fork's unselected side was transparent, which
                                // is fine, but the width must never reflow.
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
                    SizedBox(height: space.xl),
                    SizedBox(
                      width: double.infinity,
                      // Dimension: the sheet's commit CTA, same 48 as above.
                      height: 48,
                      child: ElevatedButton(
                        onPressed: () {
                          if (whatController.text.trim().isEmpty) return;
                          final argument = ArgumentData(
                            id: DateTime.now().millisecondsSinceEpoch
                                .toString(),
                            title: whatController.text.trim().length > 50
                                ? '${whatController.text.trim().substring(0, 50)}...'
                                : whatController.text.trim(),
                            explanation: whatController.text.trim(),
                            strengthIndex: strength.index,
                            createdAt: DateTime.now(),
                          );
                          parentContext.read<CaseDetailCubit>().addArgument(
                            argument,
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
                        // A button label is `control`, always — the fork's
                        // `bodyBold14` was body copy doing a control's job
                        // (M7's my_cases_page rule).
                        child: Text('დამატება', style: type.control),
                      ),
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
  }
}

class _EmptyArguments extends StatelessWidget {
  const _EmptyArguments({required this.onAdd});
  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;

    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Dimension: the oversized empty-state glyph. Every 48/64px state
          // glyph in this app was unified on `inkFaint` at M4.
          Icon(Icons.balance, size: 48, color: colors.inkFaint),
          SizedBox(height: space.l),
          Text(
            'ჯერ არ არის არგუმენტი',
            style: type.body.copyWith(color: colors.inkMute),
          ),
          SizedBox(height: space.l),
          ElevatedButton.icon(
            onPressed: onAdd,
            icon: const Icon(Icons.add),
            label: const Text('ახალი არგუმენტი'),
            style: ElevatedButton.styleFrom(
              backgroundColor: colors.actionPrimaryBg,
              foregroundColor: colors.actionPrimaryFg,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(radius.m),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ArgumentCard extends StatelessWidget {
  const _ArgumentCard({
    required this.index,
    required this.argument,
    required this.caseData,
    required this.onDelete,
  });

  final int index;
  final ArgumentData argument;
  final CaseData caseData;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return Container(
      padding: density.card,
      decoration: BoxDecoration(
        // The card GAINS the `line` hairline the fork never drew — on `ground`
        // a bare `surface` box is nearly invisible in Ink. Matches `cardTheme`
        // (M1) and `FuzzzyCard`.
        color: colors.surface,
        borderRadius: BorderRadius.circular(radius.m),
        border: Border.all(color: colors.line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                // The ⚖️ is an emoji inside a plain string with no `fontSize`
                // literal, so it is owed at M11, not this slice.
                '⚖️ არგუმენტი #$index',
                style: type.titleS.copyWith(color: colors.ink),
              ),
              const Spacer(),
              _StrengthChip(strength: argument.strength),
            ],
          ),
          SizedBox(height: space.s),
          Text(argument.title, style: type.titleS.copyWith(color: colors.ink)),
          SizedBox(height: space.xs),
          Text(
            argument.explanation,
            style: type.body.copyWith(color: colors.inkMute),
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),
          if (argument.linkedArticleIds.isNotEmpty) ...[
            SizedBox(height: space.m),
            // Colour and thickness come from dividerTheme (line, 1px).
            const Divider(height: 1),
            SizedBox(height: space.s),
            Text(
              'დაკავშირებული კანონები:',
              style: type.control.copyWith(color: colors.inkMute),
            ),
            SizedBox(height: space.xs),
            Wrap(
              spacing: space.s,
              runSpacing: space.s,
              children: argument.linkedArticleIds.map((articleId) {
                final article = caseData.linkedArticles
                    .where((a) => a.articleId == articleId)
                    .firstOrNull;
                if (article == null) return const SizedBox.shrink();
                final hasUrl = article.url != null && article.url!.isNotEmpty;

                final chip = Container(
                  padding: density.chip,
                  // The SAME citation chip the two chat surfaces draw (M6b /
                  // M8b), so M11 can swap all three onto `FuzzzyCitationChip`
                  // in one move. Parent-aware surface rule: this sits inside a
                  // `surface` card, so its recessed rung is `ground`. The gold
                  // fill, gold border and gold label all go monochrome; the
                  // tappability is carried by the underline, which survives.
                  decoration: BoxDecoration(
                    color: colors.ground,
                    borderRadius: BorderRadius.circular(radius.s),
                    border: Border.all(color: colors.line),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(Icons.gavel, size: 12, color: colors.ink),
                      SizedBox(width: space.xs),
                      Text(
                        article.title,
                        style: type.bodyS.copyWith(
                          color: colors.ink,
                          decoration: hasUrl ? TextDecoration.underline : null,
                          // Without this the rule draws in the INHERITED
                          // colour, which after the role swap is not always
                          // the text's (M8 judgement 1).
                          decorationColor: hasUrl ? colors.ink : null,
                        ),
                      ),
                      if (hasUrl) ...[
                        SizedBox(width: space.xs),
                        Icon(
                          Icons.open_in_new,
                          size: 12,
                          color: colors.inkMute,
                        ),
                      ],
                    ],
                  ),
                );

                if (!hasUrl) return chip;
                // `InkWell` → `GestureDetector(opaque)`: the kit is
                // GestureDetector-only, with zero Material ink (guard rule
                // `material-ink`, blocking).
                return GestureDetector(
                  behavior: HitTestBehavior.opaque,
                  onTap: () => launchUrl(Uri.parse(article.url!)),
                  child: chip,
                );
              }).toList(),
            ),
          ],
          if (argument.isAiGenerated) ...[
            SizedBox(height: space.s),
            Row(
              children: [
                // Provenance is META (USING §2.2), so it is `inkFaint` — the
                // fork's gold made an attribution line louder than the
                // argument it attributes. Same call as M8's facts list.
                Icon(Icons.psychology, size: 14, color: colors.inkFaint),
                SizedBox(width: space.xs),
                Text(
                  'AI-ის მიერ გენერირებული',
                  style: type.bodyS.copyWith(color: colors.inkFaint),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}

/// The strength marker on an argument card — `FuzzzyStatusChip`'s recipe,
/// app-side, for the same reason `case_chat_section._TrustBadge` is
/// (M8b §C): the kit chip labels in `fuzzzyTextStyles.label`, the uppercase
/// **mono, Latin-only** eyebrow role, and `displayNameKa` is Georgian.
///
/// Recipe copied from `fuzzzy_status_chip.dart:80-98`: no fill, a 1px
/// `Color.lerp(ground, role, 0.40)` border, `density.chip`, `radius.s`, an 8px
/// leading disc in the role, label in the role. The fork's `alpha 0.15` FILL
/// is deleted — USING §2.4 forbids alpha tints, and a red-filled "weak" badge
/// is exactly the fill USING §6 bans.
///
/// M11 consolidates this and `_TrustBadge` into one app-side status chip.
class _StrengthChip extends StatelessWidget {
  const _StrengthChip({required this.strength});
  final ArgumentStrength strength;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final role = _strengthRole(colors, strength);

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
            strength.displayNameKa,
            style: type.control.copyWith(color: role),
          ),
        ],
      ),
    );
  }
}
