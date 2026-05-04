import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

/// Case card widget displayed in the cases list.
/// Shows title, domain chip, status badge, completeness bar, and last updated.
class CaseCard extends StatelessWidget {
  const CaseCard({
    super.key,
    required this.caseData,
    required this.onTap,
    required this.onDismissed,
  });

  final CaseData caseData;
  final VoidCallback onTap;
  final VoidCallback onDismissed;

  Color _domainColor(UiColors uiColors) => switch (caseData.domain) {
    LegalDomain.criminal => uiColors.criminalColor,
    LegalDomain.civil => uiColors.civilColor,
    LegalDomain.administrative => uiColors.administrativeColor,
    LegalDomain.labor => uiColors.laborColor,
    LegalDomain.tax => uiColors.taxColor,
    LegalDomain.family => uiColors.familyColor,
    LegalDomain.property => uiColors.propertyColor,
    LegalDomain.other => uiColors.otherDomainColor,
  };

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final domainColor = _domainColor(uiColors);

    return Dismissible(
      key: ValueKey(caseData.id),
      direction: DismissDirection.endToStart,
      onDismissed: (_) => onDismissed(),
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.only(right: 20),
        decoration: BoxDecoration(
          color: uiColors.errorColor.withValues(alpha: 0.15),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Icon(Icons.archive_outlined, color: uiColors.errorColor),
      ),
      child: GestureDetector(
        onTap: onTap,
        child: Container(
          decoration: BoxDecoration(
            color: uiColors.backgroundSecondaryColor,
            borderRadius: BorderRadius.circular(12),
            border: Border(
              left: BorderSide(color: domainColor, width: 4),
            ),
          ),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Title row
              Row(
                children: [
                  Expanded(
                    child: Text(
                      caseData.title,
                      style: uiTextStyles.bodyBold16.copyWith(
                        color: uiColors.primaryTextColor,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  _StatusBadge(status: caseData.status, uiColors: uiColors, uiTextStyles: uiTextStyles),
                ],
              ),
              const SizedBox(height: 8),
              // Domain chip + date
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: domainColor.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(6),
                    ),
                    child: Text(
                      caseData.domain.shortLabelKa,
                      style: uiTextStyles.labelBold12.copyWith(color: domainColor),
                    ),
                  ),
                  const Spacer(),
                  Text(
                    _formatDate(caseData.updatedAt),
                    style: uiTextStyles.caption11.copyWith(
                      color: uiColors.secondaryTextColor,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              // Completeness bar
              Row(
                children: [
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: caseData.completenessPercent / 100,
                        backgroundColor: uiColors.surfaceColor,
                        valueColor: AlwaysStoppedAnimation(
                          caseData.completenessPercent > 60
                              ? uiColors.successColor
                              : caseData.completenessPercent > 30
                              ? uiColors.warningColor
                              : uiColors.secondaryTextColor,
                        ),
                        minHeight: 4,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    '${caseData.completenessPercent}%',
                    style: uiTextStyles.caption11.copyWith(
                      color: uiColors.secondaryTextColor,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);
    if (diff.inDays == 0) return 'დღეს';
    if (diff.inDays == 1) return 'გუშინ';
    if (diff.inDays < 7) return '${diff.inDays} დღის წინ';
    return '${date.day}.${date.month.toString().padLeft(2, '0')}.${date.year}';
  }
}

class _StatusBadge extends StatelessWidget {
  const _StatusBadge({
    required this.status,
    required this.uiColors,
    required this.uiTextStyles,
  });

  final CaseStatus status;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;

  @override
  Widget build(BuildContext context) {
    final (color, emoji) = switch (status) {
      CaseStatus.active => (uiColors.successColor, '🟢'),
      CaseStatus.pending => (uiColors.warningColor, '🟡'),
      CaseStatus.closed => (uiColors.secondaryTextColor, '⚪'),
    };

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Text(emoji, style: const TextStyle(fontSize: 10)),
        const SizedBox(width: 4),
        Text(
          status.displayNameKa,
          style: uiTextStyles.labelBold12.copyWith(color: color),
        ),
      ],
    );
  }
}
