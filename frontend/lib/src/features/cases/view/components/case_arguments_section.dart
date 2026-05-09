import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';
import 'package:url_launcher/url_launcher.dart';

/// Arguments section with numbered cards, strength badges, and guided builder.
class CaseArgumentsSection extends StatelessWidget {
  const CaseArgumentsSection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    if (caseData.arguments.isEmpty) {
      return _EmptyArguments(uiColors: uiColors, uiTextStyles: uiTextStyles, onAdd: () => _showGuidedBuilder(context));
    }

    return Column(
      children: [
        Expanded(
          child: ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: caseData.arguments.length,
            separatorBuilder: (_, __) => const SizedBox(height: 12),
            itemBuilder: (context, index) {
              final arg = caseData.arguments[index];
              return _ArgumentCard(
                index: index + 1,
                argument: arg,
                caseData: caseData,
                uiColors: uiColors,
                uiTextStyles: uiTextStyles,
                onDelete: () => context.read<CaseDetailCubit>().deleteArgument(arg.id),
              );
            },
          ),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => _showGuidedBuilder(context),
              icon: const Icon(Icons.add),
              label: const Text('ახალი არგუმენტი'),
              style: OutlinedButton.styleFrom(
                foregroundColor: uiColors.accentColor,
                side: BorderSide(color: uiColors.accentColor.withValues(alpha: 0.3)),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                padding: const EdgeInsets.symmetric(vertical: 14),
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
    final uiColors = parentContext.uiColors;
    final uiTextStyles = parentContext.uiTextStyles;

    showModalBottomSheet<void>(
      context: parentContext,
      isScrollControlled: true,
      backgroundColor: uiColors.backgroundSecondaryColor,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setSheetState) {
            return Padding(
              padding: EdgeInsets.only(left: 20, right: 20, top: 20, bottom: MediaQuery.of(ctx).viewInsets.bottom + 20),
              child: SingleChildScrollView(
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('ახალი არგუმენტი', style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor)),
                    const SizedBox(height: 20),
                    // Step 1
                    Text('ნაბიჯი 1: რა მოხდა?', style: uiTextStyles.bodyBold14.copyWith(color: uiColors.accentColor)),
                    const SizedBox(height: 8),
                    TextField(
                      controller: whatController,
                      maxLines: 3,
                      style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
                      decoration: InputDecoration(
                        hintText: 'აღწერეთ სიტუაცია...',
                        hintStyle: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor.withValues(alpha: 0.5)),
                      ),
                    ),
                    const SizedBox(height: 16),
                    // Step 2
                    Text('ნაბიჯი 2: რომელი კანონი?', style: uiTextStyles.bodyBold14.copyWith(color: uiColors.accentColor)),
                    const SizedBox(height: 8),
                    TextField(
                      controller: whichLawController,
                      style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
                      decoration: InputDecoration(
                        hintText: 'მაგ: მუხ. 316 სამოქ. კოდ.',
                        hintStyle: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor.withValues(alpha: 0.5)),
                      ),
                    ),
                    const SizedBox(height: 16),
                    // Strength selector
                    Text('სიძლიერე:', style: uiTextStyles.bodyBold14.copyWith(color: uiColors.secondaryTextColor)),
                    const SizedBox(height: 8),
                    Row(
                      children: ArgumentStrength.values.map((s) {
                        final isSelected = s == strength;
                        final color = switch (s) {
                          ArgumentStrength.strong => uiColors.successColor,
                          ArgumentStrength.moderate => uiColors.warningColor,
                          ArgumentStrength.weak => uiColors.errorColor,
                        };
                        return Expanded(
                          child: GestureDetector(
                            onTap: () => setSheetState(() => strength = s),
                            child: Container(
                              padding: const EdgeInsets.symmetric(vertical: 10),
                              margin: const EdgeInsets.symmetric(horizontal: 4),
                              decoration: BoxDecoration(
                                color: isSelected ? color.withValues(alpha: 0.2) : Colors.transparent,
                                borderRadius: BorderRadius.circular(8),
                                border: Border.all(color: isSelected ? color : uiColors.secondaryTextColor.withValues(alpha: 0.2)),
                              ),
                              child: Text(
                                s.displayNameKa,
                                textAlign: TextAlign.center,
                                style: uiTextStyles.labelBold12.copyWith(color: isSelected ? color : uiColors.secondaryTextColor),
                              ),
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 24),
                    SizedBox(
                      width: double.infinity,
                      height: 48,
                      child: ElevatedButton(
                        onPressed: () {
                          if (whatController.text.trim().isEmpty) return;
                          final argument = ArgumentData(
                            id: DateTime.now().millisecondsSinceEpoch.toString(),
                            title: whatController.text.trim().length > 50
                                ? '${whatController.text.trim().substring(0, 50)}...'
                                : whatController.text.trim(),
                            explanation: whatController.text.trim(),
                            strengthIndex: strength.index,
                            createdAt: DateTime.now(),
                          );
                          parentContext.read<CaseDetailCubit>().addArgument(argument);
                          Navigator.pop(ctx);
                        },
                        style: ElevatedButton.styleFrom(
                          backgroundColor: uiColors.accentColor,
                          foregroundColor: uiColors.backgroundPrimaryColor,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        ),
                        child: Text('დამატება', style: uiTextStyles.bodyBold14),
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
  const _EmptyArguments({required this.uiColors, required this.uiTextStyles, required this.onAdd});
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;
  final VoidCallback onAdd;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.balance, size: 48, color: uiColors.accentColor.withValues(alpha: 0.5)),
          const SizedBox(height: 16),
          Text('ჯერ არ არის არგუმენტი', style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor)),
          const SizedBox(height: 16),
          ElevatedButton.icon(
            onPressed: onAdd,
            icon: const Icon(Icons.add),
            label: const Text('ახალი არგუმენტი'),
            style: ElevatedButton.styleFrom(
              backgroundColor: uiColors.accentColor,
              foregroundColor: uiColors.backgroundPrimaryColor,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
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
    required this.uiColors,
    required this.uiTextStyles,
    required this.onDelete,
  });

  final int index;
  final ArgumentData argument;
  final CaseData caseData;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final strengthColor = switch (argument.strength) {
      ArgumentStrength.strong => uiColors.successColor,
      ArgumentStrength.moderate => uiColors.warningColor,
      ArgumentStrength.weak => uiColors.errorColor,
    };

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: uiColors.backgroundSecondaryColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                '⚖️ არგუმენტი #$index',
                style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: strengthColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  argument.strength.displayNameKa,
                  style: uiTextStyles.labelBold12.copyWith(color: strengthColor),
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(argument.title, style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor)),
          const SizedBox(height: 4),
          Text(
            argument.explanation,
            style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
          ),
          if (argument.linkedArticleIds.isNotEmpty) ...[
            const SizedBox(height: 12),
            const Divider(height: 1),
            const SizedBox(height: 8),
            Text('დაკავშირებული კანონები:', style: uiTextStyles.labelBold12.copyWith(color: uiColors.secondaryTextColor)),
            const SizedBox(height: 4),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: argument.linkedArticleIds.map((articleId) {
                final article = caseData.linkedArticles.where((a) => a.articleId == articleId).firstOrNull;
                if (article == null) return const SizedBox.shrink();
                
                return InkWell(
                  onTap: article.url != null && article.url!.isNotEmpty 
                      ? () => launchUrl(Uri.parse(article.url!)) 
                      : null,
                  borderRadius: BorderRadius.circular(6),
                  child: Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: uiColors.accentColor.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: uiColors.accentColor.withValues(alpha: 0.3)),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.gavel, size: 12, color: uiColors.accentColor),
                        const SizedBox(width: 4),
                        Text(article.title, style: uiTextStyles.labelBold12.copyWith(color: uiColors.accentColor)),
                        if (article.url != null && article.url!.isNotEmpty) ...[
                          const SizedBox(width: 4),
                          Icon(Icons.open_in_new, size: 12, color: uiColors.accentColor),
                        ],
                      ],
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
          if (argument.isAiGenerated) ...[
            const SizedBox(height: 8),
            Row(
              children: [
                Icon(Icons.psychology, size: 14, color: uiColors.accentColor),
                const SizedBox(width: 4),
                Text('AI-ის მიერ გენერირებული', style: uiTextStyles.caption11.copyWith(color: uiColors.accentColor)),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
