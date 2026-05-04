import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

/// Strategy section: primary + backup + fallback strategies with confidence.
class CaseStrategySection extends StatelessWidget {
  const CaseStrategySection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final strategy = caseData.strategy;

    if (strategy == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.shield, size: 48, color: uiColors.accentColor.withValues(alpha: 0.5)),
            const SizedBox(height: 16),
            Text('სტრატეგია ჯერ არ არის', style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor)),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              onPressed: () => _showStrategyEditor(context, null),
              icon: const Icon(Icons.add),
              label: const Text('შექმნა'),
              style: ElevatedButton.styleFrom(
                backgroundColor: uiColors.accentColor, foregroundColor: uiColors.backgroundPrimaryColor,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              ),
            ),
          ],
        ),
      );
    }

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        _StrategyCard(title: '🛡️ ძირითადი სტრატეგია', text: strategy.primaryStrategy, uiColors: uiColors, uiTextStyles: uiTextStyles),
        if (strategy.backupStrategy != null && strategy.backupStrategy!.isNotEmpty) ...[
          const SizedBox(height: 12),
          _StrategyCard(title: '🔄 სარეზერვო სტრატეგია', text: strategy.backupStrategy!, uiColors: uiColors, uiTextStyles: uiTextStyles),
        ],
        if (strategy.fallbackPosition != null && strategy.fallbackPosition!.isNotEmpty) ...[
          const SizedBox(height: 12),
          _StrategyCard(title: '🏁 ფოლბეკ პოზიცია', text: strategy.fallbackPosition!, uiColors: uiColors, uiTextStyles: uiTextStyles),
        ],
        const SizedBox(height: 16),
        // Confidence
        Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: uiColors.backgroundSecondaryColor, borderRadius: BorderRadius.circular(12)),
          child: Row(
            children: [
              Text('💪 ნდობა:', style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor)),
              const SizedBox(width: 12),
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: strategy.confidenceScore / 100,
                    backgroundColor: uiColors.surfaceColor,
                    valueColor: AlwaysStoppedAnimation(
                      strategy.confidenceScore > 60 ? uiColors.successColor : strategy.confidenceScore > 30 ? uiColors.warningColor : uiColors.errorColor,
                    ),
                    minHeight: 8,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              Text('${strategy.confidenceScore}%', style: uiTextStyles.labelBold14.copyWith(color: uiColors.primaryTextColor)),
            ],
          ),
        ),
        const SizedBox(height: 16),
        OutlinedButton.icon(
          onPressed: () => _showStrategyEditor(context, strategy),
          icon: const Icon(Icons.edit),
          label: const Text('რედაქტირება'),
          style: OutlinedButton.styleFrom(
            foregroundColor: uiColors.accentColor,
            side: BorderSide(color: uiColors.accentColor.withValues(alpha: 0.3)),
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            padding: const EdgeInsets.symmetric(vertical: 14),
          ),
        ),
      ],
    );
  }

  void _showStrategyEditor(BuildContext parentContext, StrategyData? existing) {
    final primaryController = TextEditingController(text: existing?.primaryStrategy ?? '');
    final backupController = TextEditingController(text: existing?.backupStrategy ?? '');
    final fallbackController = TextEditingController(text: existing?.fallbackPosition ?? '');
    var confidence = existing?.confidenceScore ?? 50;
    final uiColors = parentContext.uiColors;
    final uiTextStyles = parentContext.uiTextStyles;

    showModalBottomSheet<void>(
      context: parentContext,
      isScrollControlled: true,
      backgroundColor: uiColors.backgroundSecondaryColor,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setState) => Padding(
          padding: EdgeInsets.only(left: 20, right: 20, top: 20, bottom: MediaQuery.of(ctx).viewInsets.bottom + 20),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('სტრატეგია', style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor)),
                const SizedBox(height: 16),
                Text('ძირითადი სტრატეგია:', style: uiTextStyles.bodyBold14.copyWith(color: uiColors.accentColor)),
                const SizedBox(height: 8),
                TextField(controller: primaryController, maxLines: 3, style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor)),
                const SizedBox(height: 12),
                Text('სარეზერვო:', style: uiTextStyles.bodyBold14.copyWith(color: uiColors.secondaryTextColor)),
                const SizedBox(height: 8),
                TextField(controller: backupController, maxLines: 2, style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor)),
                const SizedBox(height: 12),
                Text('ფოლბეკ:', style: uiTextStyles.bodyBold14.copyWith(color: uiColors.secondaryTextColor)),
                const SizedBox(height: 8),
                TextField(controller: fallbackController, maxLines: 2, style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor)),
                const SizedBox(height: 16),
                Text('ნდობა: $confidence%', style: uiTextStyles.bodyBold14.copyWith(color: uiColors.secondaryTextColor)),
                Slider(
                  value: confidence.toDouble(), max: 100,
                  activeColor: uiColors.accentColor,
                  onChanged: (v) => setState(() => confidence = v.round()),
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity, height: 48,
                  child: ElevatedButton(
                    onPressed: () {
                      if (primaryController.text.trim().isEmpty) return;
                      parentContext.read<CaseDetailCubit>().updateStrategy(StrategyData(
                        primaryStrategy: primaryController.text.trim(),
                        backupStrategy: backupController.text.trim().isEmpty ? null : backupController.text.trim(),
                        fallbackPosition: fallbackController.text.trim().isEmpty ? null : fallbackController.text.trim(),
                        confidenceScore: confidence,
                      ));
                      Navigator.pop(ctx);
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: uiColors.accentColor, foregroundColor: uiColors.backgroundPrimaryColor,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    ),
                    child: Text('შენახვა', style: uiTextStyles.bodyBold14),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _StrategyCard extends StatelessWidget {
  const _StrategyCard({required this.title, required this.text, required this.uiColors, required this.uiTextStyles});
  final String title;
  final String text;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: uiColors.backgroundSecondaryColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor)),
          const SizedBox(height: 8),
          Text(text, style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor)),
        ],
      ),
    );
  }
}
