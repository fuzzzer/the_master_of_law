import 'package:flutter/material.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

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
    final space = context.fuzzzySpace;
    final density = context.fuzzzyDensity;

    return ListView(
      padding: density.screen,
      children: [
        // Completeness + Strength
        _StrengthCard(caseData: caseData),
        SizedBox(height: space.l),

        // Summary stats grid
        Row(
          children: [
            Expanded(
              child: _StatCard(
                // The fork used full-colour emoji ('✅ ⚖️ 📎 ⚠️') at a hardcoded
                // fontSize: 24 on an otherwise monochrome dashboard. Replaced
                // with monochrome Material glyphs (owner directive, 2026-08-11);
                // the emoji→icon table is in JOURNAL M8.
                icon: Icons.fact_check_outlined,
                label: 'ფაქტები',
                count: caseData.facts.length,
                onTap: () => onTabSwitch(3),
              ),
            ),
            SizedBox(width: space.m),
            Expanded(
              child: _StatCard(
                icon: Icons.balance,
                label: 'არგუმენტები',
                count: caseData.arguments.length,
                onTap: () => onTabSwitch(4),
              ),
            ),
          ],
        ),
        SizedBox(height: space.m),
        Row(
          children: [
            Expanded(
              child: _StatCard(
                icon: Icons.attach_file,
                label: 'მტკიცებულებები',
                count: caseData.evidence.length,
                onTap: () => onTabSwitch(5),
              ),
            ),
            SizedBox(width: space.m),
            Expanded(
              child: _StatCard(
                icon: Icons.warning_amber_outlined,
                label: 'რისკები',
                count: caseData.risks.length,
                onTap: () => onTabSwitch(8),
              ),
            ),
          ],
        ),
        SizedBox(height: space.l),

        // Strategy summary
        if (caseData.strategy != null)
          _SectionSummaryCard(
            icon: Icons.shield_outlined,
            title: 'დაცვის სტრატეგია',
            subtitle: caseData.strategy!.primaryStrategy,
            onTap: () => onTabSwitch(6),
          ),
        if (caseData.strategy != null) SizedBox(height: space.m),

        // Upcoming deadlines
        ..._buildDeadlineCards(context),

        // Action items (next 3)
        if (caseData.actionItems.isNotEmpty) ...[
          SizedBox(height: space.l),
          _ActionItemsCard(
            items: caseData.actionItems
                .where((i) => !i.isCompleted)
                .take(3)
                .toList(),
          ),
        ],

        // AI consultation CTA
        SizedBox(height: space.l),
        _AiConsultationCard(
          conversationCount: caseData.linkedConversationIds.length,
          onTap: () => onTabSwitch(1),
        ),
      ],
    );
  }

  List<Widget> _buildDeadlineCards(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    final deadlines =
        caseData.timeline
            .where(
              (e) =>
                  e.typeIndex == TimelineEventType.deadline.index &&
                  !e.isCompleted,
            )
            .toList()
          ..sort((a, b) => a.date.compareTo(b.date));

    if (deadlines.isEmpty) return [];

    return [
      SizedBox(height: space.m),
      ...deadlines.take(2).map((deadline) {
        final days = deadline.daysRemaining;
        // The ONE red voice on this screen: a deadline inside a week. The fork
        // also painted a far-off deadline `success` green — "no news" is not
        // good news, it is no news, so the third rung is now the plain `line`
        // hairline and `inkMute` copy. (The strength ring below was the other
        // traffic light; it is now monochrome, which is what frees this one to
        // stay red.)
        final urgent = days < 7;
        final rule = urgent
            ? colors.destructive
            : days < 30
            ? colors.warning
            : colors.line;
        final voice = urgent
            ? colors.destructiveText
            : days < 30
            ? colors.warning
            : colors.inkMute;

        return Padding(
          padding: EdgeInsets.only(bottom: space.s),
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTap: () => onTabSwitch(7),
            // `FuzzzyCard(leadingRule:)` again, plus the `line` hairline the
            // fork never drew on any of these cards. T-0254: the per-side
            // `Border` + `borderRadius` this used to carry throws at paint.
            child: AppRuleCard(
              rule: rule,
              borderRadius: radius.l,
              padding: density.panel,
              child: Row(
                children: [
                  Icon(Icons.timer, size: 20, color: voice),
                  SizedBox(width: space.m),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          deadline.title,
                          style: type.titleS.copyWith(color: colors.ink),
                        ),
                        Text(
                          days > 0
                              ? '$days დღე დარჩა'
                              : days == 0
                              ? 'დღეს!'
                              : '${-days} დღით ვადაგადაცილებული',
                          style: type.bodyS.copyWith(color: voice),
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
  const _StrengthCard({required this.caseData});
  final CaseData caseData;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final strength = caseData.strengthScore;

    return Container(
      padding: density.card,
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(radius.l),
        border: Border.all(color: colors.line),
      ),
      child: Row(
        children: [
          // Strength ring — `FuzzzyProgressRing`'s centre-label variant at M11.
          SizedBox(
            // Dimensions: the ring's fixed footprint.
            width: 64,
            height: 64,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CircularProgressIndicator(
                  value: strength / 100,
                  // Dimension: the ring's stroke.
                  strokeWidth: 6,
                  // The EMPTY arc is `track` (MAPPING §2.7).
                  backgroundColor: colors.track,
                  // MONOCHROME, deliberately. The fork ran a red/amber/green
                  // traffic light here, which put a `destructive` red on any
                  // case scoring under 30 — a score is an assessment, not an
                  // error, and USING §6 allows one red voice per screen. That
                  // voice is spent on the overdue-deadline rule above, which
                  // actually is time-critical. The arc's LENGTH is the signal.
                  valueColor: AlwaysStoppedAnimation(colors.ink),
                ),
                Text(
                  '$strength',
                  // A bare integer is Latin-only → the mono `data` role.
                  style: type.data.copyWith(color: colors.ink),
                ),
              ],
            ),
          ),
          SizedBox(width: space.l),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'საქმის სიძლიერე',
                  style: type.titleS.copyWith(color: colors.ink),
                ),
                SizedBox(height: space.xs),
                Text(
                  '${caseData.completenessPercent}% შევსებულია',
                  style: type.bodyS.copyWith(color: colors.inkMute),
                ),
                SizedBox(height: space.s),
                ClipRRect(
                  borderRadius: BorderRadius.circular(radius.s),
                  child: LinearProgressIndicator(
                    value: caseData.completenessPercent / 100,
                    backgroundColor: colors.track,
                    valueColor: AlwaysStoppedAnimation(colors.ink),
                    // Dimension: the bar's 4px height.
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
    required this.onTap,
  });

  final IconData icon;
  final String label;
  final int count;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;

    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: Container(
        padding: context.fuzzzyDensity.card,
        decoration: BoxDecoration(
          color: colors.surface,
          borderRadius: BorderRadius.circular(radius.l),
          border: Border.all(color: colors.line),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Dimension: the stat's leading glyph, sized to the old emoji.
            Icon(icon, size: 24, color: colors.inkMute),
            SizedBox(height: space.s),
            Text(
              '$count',
              // `FuzzzyStat`'s big numeral: a bare integer is Latin-only, so
              // the mono `dataL` role fits where `headlineBold24` used to sit.
              style: type.dataL.copyWith(color: colors.ink),
            ),
            Text(label, style: type.bodyS.copyWith(color: colors.inkMute)),
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
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;

    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: Container(
        padding: context.fuzzzyDensity.card,
        decoration: BoxDecoration(
          color: colors.surface,
          borderRadius: BorderRadius.circular(radius.l),
          border: Border.all(color: colors.line),
        ),
        child: Row(
          children: [
            Icon(icon, size: 24, color: colors.inkMute),
            SizedBox(width: space.m),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: type.titleS.copyWith(color: colors.ink)),
                  SizedBox(height: space.xs),
                  Text(
                    subtitle,
                    style: type.body.copyWith(color: colors.inkMute),
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            Icon(Icons.chevron_right, color: colors.inkMute),
          ],
        ),
      ),
    );
  }
}

class _ActionItemsCard extends StatelessWidget {
  const _ActionItemsCard({required this.items});
  final List<ActionItemData> items;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;

    return Container(
      padding: context.fuzzzyDensity.card,
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(radius.l),
        border: Border.all(color: colors.line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              // '📋' emoji → monochrome glyph (owner directive).
              Icon(Icons.checklist, size: 20, color: colors.inkMute),
              SizedBox(width: space.s),
              // M14d: same unbounded-growth class as T-0255 — a non-scaling
              // 20 px glyph plus a heading that does scale, in a Row that
              // constrained neither. Overflowed at textScaler 1.3 / 360 dp.
              Expanded(
                child: Text(
                  'სამოქმედო გეგმა',
                  style: type.titleS.copyWith(color: colors.ink),
                ),
              ),
            ],
          ),
          SizedBox(height: space.m),
          ...items.map(
            (item) => Padding(
              padding: EdgeInsets.only(bottom: space.s),
              child: Row(
                children: [
                  Icon(
                    item.isCompleted
                        ? Icons.check_box
                        : Icons.check_box_outline_blank,
                    size: 20,
                    color: item.isCompleted ? colors.success : colors.inkMute,
                  ),
                  SizedBox(width: space.s),
                  Expanded(
                    child: Text(
                      item.task,
                      style: type.body.copyWith(
                        color: item.isCompleted ? colors.inkMute : colors.ink,
                        decoration: item.isCompleted
                            ? TextDecoration.lineThrough
                            : null,
                        decorationColor: colors.inkMute,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _AiConsultationCard extends StatelessWidget {
  const _AiConsultationCard({
    required this.conversationCount,
    required this.onTap,
  });

  final int conversationCount;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;

    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: onTap,
      child: Container(
        padding: context.fuzzzyDensity.card,
        decoration: BoxDecoration(
          // The fork's gold panel at alpha 0.1 + gold border at 0.3 + gold
          // title made this the loudest card on the dashboard. Tinting a role
          // with alpha is exactly what USING §2.4 forbids; the CTA now reads as
          // a peer card whose affordance is the trailing arrow.
          color: colors.surface,
          borderRadius: BorderRadius.circular(radius.l),
          border: Border.all(color: colors.lineStrong),
        ),
        child: Row(
          children: [
            // Dimension: the CTA's oversized leading glyph.
            Icon(Icons.psychology, size: 32, color: colors.ink),
            SizedBox(width: space.m),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'AI კონსულტაცია',
                    style: type.titleS.copyWith(color: colors.ink),
                  ),
                  Text(
                    conversationCount > 0
                        ? '$conversationCount კონსულტაცია'
                        : 'დაიწყეთ პირველი კონსულტაცია',
                    style: type.bodyS.copyWith(color: colors.inkMute),
                  ),
                ],
              ),
            ),
            Icon(Icons.arrow_forward, color: colors.ink),
          ],
        ),
      ),
    );
  }
}
