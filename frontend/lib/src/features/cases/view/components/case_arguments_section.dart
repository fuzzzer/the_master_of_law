import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
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
/// Argument strength as an [AppStatusKind]. This is the single source of the
/// mapping; [_strengthRole] derives its colour from it so the 4px leading rule
/// and the chip can never disagree.
AppStatusKind _strengthKind(ArgumentStrength s) => switch (s) {
  ArgumentStrength.strong => AppStatusKind.success,
  ArgumentStrength.moderate => AppStatusKind.warning,
  ArgumentStrength.weak => AppStatusKind.error,
};

Color _strengthRole(FuzzzyColors c, ArgumentStrength s) =>
    switch (_strengthKind(
      s,
    )) {
      AppStatusKind.success => c.success,
      AppStatusKind.warning => c.warning,
      AppStatusKind.error => c.destructive,
      AppStatusKind.info => c.info,
      AppStatusKind.neutral => c.inkMute,
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
              // M11b: ⚖️ → `Icons.balance`, the same glyph M8 gave the
              // "არგუმენტები" stat card and M11b gave the tab.
              Icon(Icons.balance, size: 20, color: colors.inkMute),
              SizedBox(width: space.s),
              // 🔴 T-0255 (M14d). This `Text` and the chip were both
              // unconstrained, so both took their natural width and the row
              // overflowed by 2.9 px at textScaler 1.3 / 360 dp — the
              // unbounded-growth mode contract §3.1.13 predicts for this app.
              //
              // `Expanded` + a fixed gap, NOT `Spacer`. `Spacer` is itself a
              // flex child, so keeping it here would split the free space
              // 50/50 with the title and make it wrap at every width. With the
              // title expanded, the chip is still pushed hard right — the
              // Spacer's only job — and the title now wraps instead of
              // overflowing. Deliberately NO `maxLines`/`ellipsis`: an
              // ellipsis at this width would eat the argument's own index
              // number, and truncating text is a defect in its own right
              // (plan §4), not a fix for one.
              Expanded(
                child: Text(
                  'არგუმენტი #$index',
                  style: type.titleS.copyWith(color: colors.ink),
                ),
              ),
              SizedBox(width: space.s),
              AppStatusChip(
                label: argument.strength.displayNameKa,
                kind: _strengthKind(argument.strength),
                qaId: 'argStrength.$index',
              ),
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

                // M11d: the fourth and last hand-rolled citation chip, now
                // `AppCitationChip`. Sits inside a `surface` argument card, so
                // `parent: surface` gives it a `ground` box.
                return AppCitationChip(
                  label: article.title,
                  parent: AppChipParent.surface,
                  leading: const Icon(Icons.gavel),
                  trailing: hasUrl ? const Icon(Icons.open_in_new) : null,
                  onTap: hasUrl
                      ? () => launchUrl(Uri.parse(article.url!))
                      : null,
                  qaId: article.articleId,
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
                // M14d: same unbounded-growth class as T-0255 one card up.
                // The 14 px icon does NOT scale with textScaler while the
                // label does, so the row's fixed overhead stays put while its
                // text grows. `Expanded` is the idiom `case_risks_section`'s
                // mitigation row already uses two lines above its own copy of
                // this bug.
                Expanded(
                  child: Text(
                    'AI-ის მიერ გენერირებული',
                    style: type.bodyS.copyWith(color: colors.inkFaint),
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
