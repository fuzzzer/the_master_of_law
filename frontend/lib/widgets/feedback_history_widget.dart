import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

/// Widget that displays past feedback entries for a given case or conversation.
///
/// Shows a list of feedback cards with star rating, category chip,
/// comment preview, and timestamp.
///
/// Usage:
/// ```dart
/// FeedbackHistoryWidget(
///   targetType: 'case_file',
///   targetId: caseData.id,
/// )
/// ```
class FeedbackHistoryWidget extends StatelessWidget {
  const FeedbackHistoryWidget({
    super.key,
    required this.targetType,
    required this.targetId,
  });

  final String targetType;
  final String targetId;

  static const Map<String, String> _categoryLabels = {
    'accuracy': 'სიზუსტე',
    'completeness': 'სრულყოფილება',
    'relevance': 'რელევანტურობა',
    'formatting': 'ფორმატირება',
    'citation_quality': 'ციტირება',
    'legal_reasoning': 'იურიდ. არგუმენტაცია',
    'overall': 'საერთო',
  };

  static const Map<String, String> _reviewerLabels = {
    'tester': 'ტესტერი',
    'legal_expert': 'იურისტი',
    'user': 'მომხმარებელი',
    'anonymous': 'ანონიმი',
  };

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    // TODO: Replace with actual API call when integration is done.
    // For now, shows a placeholder state.
    final hasFeedback = false;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Text(
              'შეფასებები',
              style: uiTextStyles.bodyBold16.copyWith(
                color: uiColors.primaryTextColor,
              ),
            ),
            const Spacer(),
            // Average rating placeholder
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: uiColors.warningColor.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(20),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(Icons.star_rounded, size: 14, color: uiColors.warningColor),
                  const SizedBox(width: 4),
                  Text(
                    '--',
                    style: uiTextStyles.labelBold12.copyWith(
                      color: uiColors.warningColor,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),
        if (!hasFeedback)
          _EmptyState(uiColors: uiColors, uiTextStyles: uiTextStyles)
        else
          // TODO: Render fetched feedback list
          const SizedBox.shrink(),
      ],
    );
  }

  /// Builds a single feedback card.
  static Widget buildFeedbackCard({
    required BuildContext context,
    required String category,
    required int rating,
    String? comment,
    String? specificSection,
    required String reviewerType,
    required DateTime createdAt,
  }) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: uiColors.backgroundSecondaryColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Top row: category + rating + reviewer
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: uiColors.accentColor.withValues(alpha: 0.15),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  _categoryLabels[category] ?? category,
                  style: uiTextStyles.labelBold12.copyWith(
                    color: uiColors.accentColor,
                  ),
                ),
              ),
              const Spacer(),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: List.generate(5, (index) {
                  return Icon(
                    index < rating ? Icons.star_rounded : Icons.star_border_rounded,
                    size: 16,
                    color: index < rating ? uiColors.warningColor : uiColors.secondaryTextColor,
                  );
                }),
              ),
            ],
          ),
          const SizedBox(height: 8),
          // Comment
          if (comment != null && comment.isNotEmpty)
            Text(
              comment,
              style: uiTextStyles.body14.copyWith(
                color: uiColors.primaryTextColor,
              ),
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
          if (comment != null && comment.isNotEmpty)
            const SizedBox(height: 8),
          // Section tag
          if (specificSection != null && specificSection.isNotEmpty)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: uiColors.surfaceColor,
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                'სექცია: $specificSection',
                style: uiTextStyles.caption11.copyWith(
                  color: uiColors.secondaryTextColor,
                ),
              ),
            ),
          if (specificSection != null && specificSection.isNotEmpty)
            const SizedBox(height: 8),
          // Footer: reviewer type + date
          Row(
            children: [
              Text(
                _reviewerLabels[reviewerType] ?? reviewerType,
                style: uiTextStyles.caption11.copyWith(
                  color: uiColors.secondaryTextColor,
                ),
              ),
              const Spacer(),
              Text(
                _formatDate(createdAt),
                style: uiTextStyles.caption11.copyWith(
                  color: uiColors.secondaryTextColor,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  static String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);
    if (diff.inDays == 0) return 'დღეს';
    if (diff.inDays == 1) return 'გუშინ';
    if (diff.inDays < 7) return '${diff.inDays} დღის წინ';
    return '${date.day}.${date.month.toString().padLeft(2, '0')}.${date.year}';
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({
    required this.uiColors,
    required this.uiTextStyles,
  });

  final UiColors uiColors;
  final UiTextStyles uiTextStyles;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 24),
        child: Column(
          children: [
            Icon(
              Icons.rate_review_outlined,
              size: 48,
              color: uiColors.secondaryTextColor.withValues(alpha: 0.4),
            ),
            const SizedBox(height: 12),
            Text(
              'ჯერ არ არის შეფასებები',
              style: uiTextStyles.body14.copyWith(
                color: uiColors.secondaryTextColor,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              'იყავით პირველი და გაგვიზიარეთ აზრი',
              style: uiTextStyles.caption11.copyWith(
                color: uiColors.secondaryTextColor.withValues(alpha: 0.7),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
