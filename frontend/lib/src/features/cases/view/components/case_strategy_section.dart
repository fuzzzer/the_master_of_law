import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:url_launcher/url_launcher.dart';

/// Strategy section: primary + backup + fallback strategies with confidence.
class CaseStrategySection extends StatelessWidget {
  const CaseStrategySection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final strategy = caseData.strategy;

    if (strategy == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Dimension: the oversized empty-state glyph, on M4's `inkFaint`.
            Icon(Icons.shield, size: 48, color: colors.inkFaint),
            SizedBox(height: space.l),
            Text(
              'სტრატეგია ჯერ არ არის',
              style: type.body.copyWith(color: colors.inkMute),
            ),
            SizedBox(height: space.l),
            ElevatedButton.icon(
              onPressed: () => _showStrategyEditor(context, null),
              icon: const Icon(Icons.add),
              label: const Text('შექმნა'),
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

    return ListView(
      padding: density.screen,
      children: [
        // M11b: the 🛡️/🔄/🏁/💪 emoji came OUT of the label strings and became
        // a real `icon` slot on the card — see the JOURNAL M11b table.
        _StrategyCard(
          icon: Icons.shield_outlined,
          title: 'ძირითადი სტრატეგია',
          text: strategy.primaryStrategy,
        ),
        if (strategy.backupStrategy != null &&
            strategy.backupStrategy!.isNotEmpty) ...[
          SizedBox(height: space.m),
          _StrategyCard(
            icon: Icons.alt_route,
            title: 'სარეზერვო სტრატეგია',
            text: strategy.backupStrategy!,
          ),
        ],
        if (strategy.fallbackPosition != null &&
            strategy.fallbackPosition!.isNotEmpty) ...[
          SizedBox(height: space.m),
          _StrategyCard(
            icon: Icons.flag_outlined,
            title: 'ფოლბეკ პოზიცია',
            text: strategy.fallbackPosition!,
          ),
        ],
        SizedBox(height: space.l),
        // Confidence
        Container(
          padding: density.card,
          decoration: BoxDecoration(
            color: colors.surface,
            borderRadius: BorderRadius.circular(radius.m),
            // The card GAINS the `line` hairline the fork never drew.
            border: Border.all(color: colors.line),
          ),
          child: Row(
            children: [
              Icon(Icons.speed, size: 20, color: colors.inkMute),
              SizedBox(width: space.s),
              Text('ნდობა:', style: type.titleS.copyWith(color: colors.ink)),
              SizedBox(width: space.m),
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(radius.l),
                  child: LinearProgressIndicator(
                    value: strategy.confidenceScore / 100,
                    // MAPPING §2.7: the EMPTY progress track is `track`, the
                    // role the recipe thought the fork had no field for. It
                    // had one; it called it `surfaceColor`.
                    backgroundColor: colors.track,
                    // 🔴 THE THIRD TRAFFIC LIGHT, DEMOTED. The fork ran a
                    // red/amber/green ramp on `confidenceScore` (>60 / >30 /
                    // else) — the identical shape M8 §B demoted on the strength
                    // ring and M7 demoted on the completeness bar. A confidence
                    // score is an ASSESSMENT, not an error: painting a case at
                    // 29% in `destructive` tells the user their case is broken.
                    // **The bar's LENGTH is the signal**, and the numeral beside
                    // it says the rest.
                    valueColor: AlwaysStoppedAnimation(colors.ink),
                    // Dimension: the bar's own thickness, matching M8's
                    // completeness bar.
                    minHeight: 8,
                  ),
                ),
              ),
              SizedBox(width: space.s),
              Text(
                '${strategy.confidenceScore}%',
                // Latin-only and tabular, so it CAN take the mono role — the
                // M6b/M7/M8 test is the STRING, not the datum.
                style: type.data.copyWith(color: colors.ink),
              ),
            ],
          ),
        ),
        if (strategy.supportingArticleIds.isNotEmpty) ...[
          SizedBox(height: space.l),
          Text(
            'სამართლებრივი საფუძვლები:',
            style: type.control.copyWith(color: colors.inkMute),
          ),
          SizedBox(height: space.s),
          Wrap(
            spacing: space.s,
            runSpacing: space.s,
            children: strategy.supportingArticleIds.map((articleId) {
              final article = caseData.linkedArticles
                  .where((a) => a.articleId == articleId)
                  .firstOrNull;
              if (article == null) return const SizedBox.shrink();
              final hasUrl = article.url != null && article.url!.isNotEmpty;

              // M11d: the third of four hand-rolled citation chips, now
              // `AppCitationChip`. This one sits directly on the list's
              // `ground`, so `parent: ground` gives it a `surface` box — the
              // parent-aware rule running the other way from the two chat
              // surfaces, which is exactly why it is an argument and not a
              // constant.
              return AppCitationChip(
                label: article.title,
                parent: AppCitationParent.ground,
                leading: const Icon(Icons.gavel),
                trailing: hasUrl ? const Icon(Icons.open_in_new) : null,
                onTap: hasUrl ? () => launchUrl(Uri.parse(article.url!)) : null,
                qaId: article.articleId,
              );
            }).toList(),
          ),
        ],
        SizedBox(height: space.l),
        SizedBox(
          // Dimension: the full-width CTA height (M8's add-fact button).
          height: 48,
          child: OutlinedButton.icon(
            onPressed: () => _showStrategyEditor(context, strategy),
            icon: const Icon(Icons.edit),
            label: const Text('რედაქტირება'),
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
      ],
    );
  }

  void _showStrategyEditor(BuildContext parentContext, StrategyData? existing) {
    final primaryController = TextEditingController(
      text: existing?.primaryStrategy ?? '',
    );
    final backupController = TextEditingController(
      text: existing?.backupStrategy ?? '',
    );
    final fallbackController = TextEditingController(
      text: existing?.fallbackPosition ?? '',
    );
    var confidence = existing?.confidenceScore ?? 50;

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
                    'სტრატეგია',
                    style: type.titleM.copyWith(color: colors.ink),
                  ),
                  SizedBox(height: space.l),
                  // The fork gave the primary label gold and the other two
                  // grey. That hierarchy survives as an INK RUNG (`ink` vs
                  // `inkMute`) rather than a hue — MAPPING §2.2 judgement 1.
                  Text(
                    'ძირითადი სტრატეგია:',
                    style: type.control.copyWith(color: colors.ink),
                  ),
                  SizedBox(height: space.s),
                  TextField(
                    controller: primaryController,
                    maxLines: 3,
                    style: type.body.copyWith(color: colors.fieldText),
                  ),
                  SizedBox(height: space.m),
                  Text(
                    'სარეზერვო:',
                    style: type.control.copyWith(color: colors.inkMute),
                  ),
                  SizedBox(height: space.s),
                  TextField(
                    controller: backupController,
                    maxLines: 2,
                    style: type.body.copyWith(color: colors.fieldText),
                  ),
                  SizedBox(height: space.m),
                  Text(
                    'ფოლბეკ:',
                    style: type.control.copyWith(color: colors.inkMute),
                  ),
                  SizedBox(height: space.s),
                  TextField(
                    controller: fallbackController,
                    maxLines: 2,
                    style: type.body.copyWith(color: colors.fieldText),
                  ),
                  SizedBox(height: space.l),
                  Text(
                    'ნდობა: $confidence%',
                    style: type.control.copyWith(color: colors.inkMute),
                  ),
                  Slider(
                    value: confidence.toDouble(),
                    max: 100,
                    // MAPPING §2.2: `Slider.activeColor` is the FILL of a
                    // primary action → `actionPrimaryBg`. The inactive half
                    // is the empty `track`.
                    activeColor: colors.actionPrimaryBg,
                    inactiveColor: colors.track,
                    onChanged: (v) => setState(() => confidence = v.round()),
                  ),
                  SizedBox(height: space.l),
                  SizedBox(
                    width: double.infinity,
                    // Dimension: the sheet's commit CTA.
                    height: 48,
                    child: ElevatedButton(
                      onPressed: () {
                        if (primaryController.text.trim().isEmpty) return;
                        parentContext.read<CaseDetailCubit>().updateStrategy(
                          StrategyData(
                            primaryStrategy: primaryController.text.trim(),
                            backupStrategy: backupController.text.trim().isEmpty
                                ? null
                                : backupController.text.trim(),
                            fallbackPosition:
                                fallbackController.text.trim().isEmpty
                                ? null
                                : fallbackController.text.trim(),
                            confidenceScore: confidence,
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
                      child: Text('შენახვა', style: type.control),
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

class _StrategyCard extends StatelessWidget {
  const _StrategyCard({
    required this.icon,
    required this.title,
    required this.text,
  });

  /// Monochrome Material glyph. It replaces the emoji the fork interpolated
  /// into [title] itself — a picture living inside a translated string, which
  /// no `type` role could size and no colour role could tint.
  final IconData icon;
  final String title;
  final String text;

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
        color: colors.surface,
        borderRadius: BorderRadius.circular(radius.m),
        // The card GAINS the `line` hairline the fork never drew.
        border: Border.all(color: colors.line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(icon, size: 20, color: colors.inkMute),
              SizedBox(width: space.s),
              Expanded(
                child: Text(
                  title,
                  style: type.titleS.copyWith(color: colors.ink),
                ),
              ),
            ],
          ),
          SizedBox(height: space.s),
          Text(text, style: type.body.copyWith(color: colors.inkMute)),
        ],
      ),
    );
  }
}
