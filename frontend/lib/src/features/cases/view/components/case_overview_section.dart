import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

/// Bird's-eye overview dashboard with summary cards.
/// Each card tappable → navigates to corresponding tab.
class CaseOverviewSection extends StatelessWidget {
  const CaseOverviewSection({
    super.key,
    required this.caseData,
    required this.onTabSwitch,
  });

  final CaseData caseData;
  final ValueChanged<int> onTabSwitch;

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        // Completeness + Strength
        _StrengthCard(caseData: caseData, uiColors: uiColors, uiTextStyles: uiTextStyles),
        const SizedBox(height: 16),

        // Summary stats grid
        Row(
          children: [
            Expanded(child: _StatCard(
              icon: '✅',
              label: 'ფაქტები',
              count: caseData.facts.length,
              uiColors: uiColors,
              uiTextStyles: uiTextStyles,
              onTap: () => onTabSwitch(3),
            )),
            const SizedBox(width: 12),
            Expanded(child: _StatCard(
              icon: '⚖️',
              label: 'არგუმენტები',
              count: caseData.arguments.length,
              uiColors: uiColors,
              uiTextStyles: uiTextStyles,
              onTap: () => onTabSwitch(4),
            )),
          ],
        ),
        const SizedBox(height: 12),
        Row(
          children: [
            Expanded(child: _StatCard(
              icon: '📎',
              label: 'მტკიცებულებები',
              count: caseData.evidence.length,
              uiColors: uiColors,
              uiTextStyles: uiTextStyles,
              onTap: () => onTabSwitch(5),
            )),
            const SizedBox(width: 12),
            Expanded(child: _StatCard(
              icon: '⚠️',
              label: 'რისკები',
              count: caseData.risks.length,
              uiColors: uiColors,
              uiTextStyles: uiTextStyles,
              onTap: () => onTabSwitch(8),
            )),
          ],
        ),
        const SizedBox(height: 16),

        // Strategy summary
        if (caseData.strategy != null)
          _SectionSummaryCard(
            icon: '🛡️',
            title: 'დაცვის სტრატეგია',
            subtitle: caseData.strategy!.primaryStrategy,
            uiColors: uiColors,
            uiTextStyles: uiTextStyles,
            onTap: () => onTabSwitch(6),
          ),
        if (caseData.strategy != null) const SizedBox(height: 12),

        // Upcoming deadlines
        ..._buildDeadlineCards(uiColors, uiTextStyles),

        // Action items (next 3)
        if (caseData.actionItems.isNotEmpty) ...[
          const SizedBox(height: 16),
          _ActionItemsCard(
            items: caseData.actionItems.where((i) => !i.isCompleted).take(3).toList(),
            uiColors: uiColors,
            uiTextStyles: uiTextStyles,
          ),
        ],

        // AI consultation CTA
        const SizedBox(height: 16),
        _AiConsultationCard(
          conversationCount: caseData.linkedConversationIds.length,
          uiColors: uiColors,
          uiTextStyles: uiTextStyles,
          onTap: () => onTabSwitch(1),
        ),
      ],
    );
  }

  List<Widget> _buildDeadlineCards(UiColors uiColors, UiTextStyles uiTextStyles) {
    final deadlines = caseData.timeline
        .where((e) => e.typeIndex == TimelineEventType.deadline.index && !e.isCompleted)
        .toList()
      ..sort((a, b) => a.date.compareTo(b.date));

    if (deadlines.isEmpty) return [];

    return [
      const SizedBox(height: 12),
      ...deadlines.take(2).map((deadline) {
        final days = deadline.daysRemaining;
        final urgencyColor = days < 7
            ? uiColors.errorColor
            : days < 30
                ? uiColors.warningColor
                : uiColors.successColor;

        return Padding(
          padding: const EdgeInsets.only(bottom: 8),
          child: GestureDetector(
            onTap: () => onTabSwitch(7),
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: uiColors.backgroundSecondaryColor,
                borderRadius: BorderRadius.circular(12),
                border: Border(left: BorderSide(color: urgencyColor, width: 4)),
              ),
              child: Row(
                children: [
                  Icon(Icons.timer, size: 20, color: urgencyColor),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          deadline.title,
                          style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
                        ),
                        Text(
                          days > 0 ? '$days დღე დარჩა' : days == 0 ? 'დღეს!' : '${-days} დღით ვადაგადაცილებული',
                          style: uiTextStyles.caption11.copyWith(color: urgencyColor),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      }),
    ];
  }
}

class _StrengthCard extends StatelessWidget {
  const _StrengthCard({required this.caseData, required this.uiColors, required this.uiTextStyles});
  final CaseData caseData;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;

  @override
  Widget build(BuildContext context) {
    final strength = caseData.strengthScore;
    final strengthColor = strength > 60
        ? uiColors.successColor
        : strength > 30
            ? uiColors.warningColor
            : uiColors.errorColor;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: uiColors.backgroundSecondaryColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        children: [
          // Strength ring
          SizedBox(
            width: 64,
            height: 64,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CircularProgressIndicator(
                  value: strength / 100,
                  strokeWidth: 6,
                  backgroundColor: uiColors.surfaceColor,
                  valueColor: AlwaysStoppedAnimation(strengthColor),
                ),
                Text(
                  '$strength',
                  style: uiTextStyles.headlineBold20.copyWith(color: strengthColor),
                ),
              ],
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'საქმის სიძლიერე',
                  style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
                ),
                const SizedBox(height: 4),
                Text(
                  '${caseData.completenessPercent}% შევსებულია',
                  style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                ),
                const SizedBox(height: 8),
                ClipRRect(
                  borderRadius: BorderRadius.circular(4),
                  child: LinearProgressIndicator(
                    value: caseData.completenessPercent / 100,
                    backgroundColor: uiColors.surfaceColor,
                    valueColor: AlwaysStoppedAnimation(uiColors.accentColor),
                    minHeight: 4,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  const _StatCard({
    required this.icon,
    required this.label,
    required this.count,
    required this.uiColors,
    required this.uiTextStyles,
    required this.onTap,
  });

  final String icon;
  final String label;
  final int count;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: uiColors.backgroundSecondaryColor,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(icon, style: const TextStyle(fontSize: 24)),
            const SizedBox(height: 8),
            Text(
              '$count',
              style: uiTextStyles.headlineBold24.copyWith(color: uiColors.primaryTextColor),
            ),
            Text(
              label,
              style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
            ),
          ],
        ),
      ),
    );
  }
}

class _SectionSummaryCard extends StatelessWidget {
  const _SectionSummaryCard({
    required this.icon,
    required this.title,
    required this.subtitle,
    required this.uiColors,
    required this.uiTextStyles,
    required this.onTap,
  });

  final String icon;
  final String title;
  final String subtitle;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: uiColors.backgroundSecondaryColor,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Row(
          children: [
            Text(icon, style: const TextStyle(fontSize: 24)),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor)),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            Icon(Icons.chevron_right, color: uiColors.secondaryTextColor),
          ],
        ),
      ),
    );
  }
}

class _ActionItemsCard extends StatelessWidget {
  const _ActionItemsCard({required this.items, required this.uiColors, required this.uiTextStyles});
  final List<ActionItemData> items;
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
          Text('📋 სამოქმედო გეგმა', style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor)),
          const SizedBox(height: 12),
          ...items.map((item) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Row(
                  children: [
                    Icon(
                      item.isCompleted ? Icons.check_box : Icons.check_box_outline_blank,
                      size: 20,
                      color: item.isCompleted ? uiColors.successColor : uiColors.secondaryTextColor,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        item.task,
                        style: uiTextStyles.body14.copyWith(
                          color: uiColors.primaryTextColor,
                          decoration: item.isCompleted ? TextDecoration.lineThrough : null,
                        ),
                      ),
                    ),
                  ],
                ),
              )),
        ],
      ),
    );
  }
}

class _AiConsultationCard extends StatelessWidget {
  const _AiConsultationCard({
    required this.conversationCount,
    required this.uiColors,
    required this.uiTextStyles,
    required this.onTap,
  });

  final int conversationCount;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: uiColors.accentColor.withValues(alpha: 0.1),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: uiColors.accentColor.withValues(alpha: 0.3)),
        ),
        child: Row(
          children: [
            Icon(Icons.psychology, size: 32, color: uiColors.accentColor),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'AI კონსულტაცია',
                    style: uiTextStyles.bodyBold14.copyWith(color: uiColors.accentColor),
                  ),
                  Text(
                    conversationCount > 0
                        ? '$conversationCount კონსულტაცია'
                        : 'დაიწყეთ პირველი კონსულტაცია',
                    style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                  ),
                ],
              ),
            ),
            Icon(Icons.arrow_forward, color: uiColors.accentColor),
          ],
        ),
      ),
    );
  }
}
