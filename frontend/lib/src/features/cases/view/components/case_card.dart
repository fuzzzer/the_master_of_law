import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:themasteroflaw/src/src.dart';

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

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    // The one place a taxonomy colour is read: it paints the 4px leading rule
    // and the chip's 8px dot, and nothing else (see LegalDomainColors).
    final domainColor = context.legalDomainColors.of(caseData.domain);

    return Dismissible(
      key: ValueKey(caseData.id),
      direction: DismissDirection.endToStart,
      onDismissed: (_) => onDismissed(),
      background: Container(
        alignment: Alignment.centerRight,
        padding: EdgeInsets.only(right: space.xl),
        decoration: BoxDecoration(
          // Swipe-to-archive IS a destructive commit in flight, which is the
          // one moment USING §6 duty 4 allows red as a fill.
          color: colors.destructive,
          borderRadius: BorderRadius.circular(radius.l),
        ),
        child: Icon(Icons.archive_outlined, color: colors.onRed),
      ),
      child: GestureDetector(
        behavior: HitTestBehavior.opaque,
        onTap: onTap,
        // `FuzzzyCard(leadingRule:)`'s shape (containers/fuzzzy_card.dart) —
        // the fork's AccentCard idiom. The card also gains the hairline the
        // fork never drew: a `surface` box on `ground` needs a `line` edge in
        // Ink. T-0254: this used to be a per-side `Border` + `borderRadius`,
        // which throws at paint; `AppRuleCard` carries the kit's real idiom.
        child: AppRuleCard(
          rule: domainColor,
          borderRadius: radius.l,
          padding: density.card,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Title row
              Row(
                children: [
                  Expanded(
                    child: Text(
                      caseData.title,
                      style: type.titleS.copyWith(color: colors.ink),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  SizedBox(width: space.s),
                  AppStatusChip(
                    label: caseData.status.displayNameKa,
                    kind: caseStatusKind(caseData.status),
                    qaId: 'caseStatus.${caseData.id}',
                  ),
                ],
              ),
              SizedBox(height: space.s),
              // Domain chip + date
              Row(
                children: [
                  AppDomainChip(
                    domain: caseData.domain,
                    // Inside a `surface` card -> a `ground` box.
                    parent: AppChipParent.surface,
                    qaId: 'caseDomain.${caseData.id}',
                  ),
                  const Spacer(),
                  Text(
                    _formatDate(caseData.updatedAt),
                    style: type.bodyS.copyWith(color: colors.inkFaint),
                  ),
                ],
              ),
              SizedBox(height: space.m),
              // Completeness bar
              Row(
                children: [
                  Expanded(
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(radius.s),
                      child: LinearProgressIndicator(
                        value: caseData.completenessPercent / 100,
                        // The EMPTY half of a progress bar is `track`, not
                        // `surface` (MAPPING §2.7 — the fork's `surfaceColor`
                        // was the track role wearing the wrong name).
                        backgroundColor: colors.track,
                        // Completeness is progress, not a verdict: a
                        // three-colour traffic light here would spend two
                        // semantic roles on a percentage. One `ink` bar, and
                        // the number next to it says the rest.
                        valueColor: AlwaysStoppedAnimation(colors.ink),
                        // Dimension: the bar's own 4px height.
                        minHeight: 4,
                      ),
                    ),
                  ),
                  SizedBox(width: space.s),
                  Text(
                    '${caseData.completenessPercent}%',
                    // A percentage is tabular data and carries no Georgian —
                    // one of the very few strings in this app that CAN take
                    // the mono `dataS` role (see JOURNAL M6b judgement 4).
                    style: type.dataS.copyWith(color: colors.inkMute),
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

/// A case's lifecycle status as an [AppStatusKind]. Shared by this card and by
/// `case_workspace_page`'s app-bar chip — M11c collapsed the two byte-identical
/// `_StatusBadge` / `_StatusChip` twins onto [AppStatusChip], and this is the
/// one place the mapping lives.
///
/// The fork drew this state twice: once as a colour and once as a coloured
/// emoji (🟢/🟡/⚪ at a hardcoded `fontSize: 10`). The chip's 8px disc IS what
/// the emoji was imitating, so the emoji was deleted rather than re-sized.
AppStatusKind caseStatusKind(CaseStatus status) => switch (status) {
  CaseStatus.active => AppStatusKind.success,
  CaseStatus.pending => AppStatusKind.warning,
  CaseStatus.closed => AppStatusKind.neutral,
};
