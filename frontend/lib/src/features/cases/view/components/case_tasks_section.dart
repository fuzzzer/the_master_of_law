import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

/// Combined tasks + clarifications section for the case workspace.
class CaseTasksSection extends StatelessWidget {
  const CaseTasksSection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final cubit = context.read<CaseDetailCubit>();

    return BlocBuilder<CaseDetailCubit, CaseDetailState>(
      builder: (context, state) {
        final data = state.caseData ?? caseData;

        return ListView(
          padding: density.screen,
          children: [
            // ── Clarifications ──
            if (data.clarifications.isNotEmpty) ...[
              _SectionHeader(
                icon: Icons.help_outline,
                title: 'დასაზუსტებელი ინფორმაცია',
                count: data.clarifications.where((c) => !c.isResolved).length,
              ),
              SizedBox(height: space.s),
              ...data.clarifications.map(
                (item) => _ClarificationTile(
                  item: item,
                  onToggle: () => cubit.toggleClarification(item.id),
                  onDelete: () => cubit.deleteClarification(item.id),
                ),
              ),
              SizedBox(height: space.xl),
            ],

            // ── Action Items (Tasks) ──
            _SectionHeader(
              icon: Icons.checklist,
              title: 'დავალებები',
              count: data.actionItems.where((i) => !i.isCompleted).length,
            ),
            SizedBox(height: space.s),
            if (data.actionItems.isEmpty)
              const _EmptyState(text: 'დავალებები ჯერ არ არის'),
            ...data.actionItems.map(
              (item) => _ActionItemTile(
                item: item,
                onToggle: () => cubit.toggleActionItem(item.id),
                onDelete: () => cubit.deleteActionItem(item.id),
                onEdit: (newText) {
                  item.task = newText;
                  cubit.updateActionItemText(item.id, newText);
                },
              ),
            ),
            SizedBox(height: space.l),

            // ── Add Task Button ──
            OutlinedButton.icon(
              onPressed: () => _showAddTaskDialog(context, cubit),
              icon: const Icon(Icons.add, size: 18),
              label: const Text('დავალების დამატება'),
              // `FuzzzyButton.secondary`: `ink` label on a `lineStrong` outline.
              style: OutlinedButton.styleFrom(
                foregroundColor: colors.ink,
                side: BorderSide(color: colors.lineStrong),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(radius.m),
                ),
                padding: density.snug,
                textStyle: type.control,
              ),
            ),
          ],
        );
      },
    );
  }

  void _showAddTaskDialog(BuildContext context, CaseDetailCubit cubit) {
    final controller = TextEditingController();
    showDialog<void>(
      context: context,
      builder: (ctx) {
        final colors = ctx.fuzzzyColors;
        final type = ctx.fuzzzyTextStyles;
        final radius = ctx.fuzzzyRadius;
        return AlertDialog(
          // Overlay rung: `raised` + `lineStrong`. The fork used
          // `backgroundPrimaryColor` here — the PAGE colour — so the dialog was
          // indistinguishable from what it floated over (MAPPING §2.5's trap).
          backgroundColor: colors.raised,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radius.l),
            side: BorderSide(color: colors.lineStrong),
          ),
          title: Text(
            'ახალი დავალება',
            style: type.titleS.copyWith(color: colors.ink),
          ),
          content: TextField(
            controller: controller,
            autofocus: true,
            maxLines: 3,
            style: type.body.copyWith(color: colors.fieldText),
            // Box + hint come from M1's inputDecorationTheme.
            decoration: const InputDecoration(hintText: 'რა უნდა გაკეთდეს...'),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: Text(
                'გაუქმება',
                style: type.control.copyWith(color: colors.inkMute),
              ),
            ),
            TextButton(
              onPressed: () {
                final text = controller.text.trim();
                if (text.isNotEmpty) {
                  cubit.addActionItem(
                    ActionItemData(
                      id: 'user_task_${DateTime.now().millisecondsSinceEpoch}',
                      task: text,
                      priorityIndex: ActionPriority.medium.index,
                    ),
                  );
                }
                Navigator.pop(ctx);
              },
              child: Text(
                'დამატება',
                style: type.control.copyWith(color: colors.ink),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({
    required this.icon,
    required this.title,
    required this.count,
  });
  final IconData icon;
  final String title;
  final int count;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;

    return Row(
      children: [
        Icon(icon, size: 20, color: colors.ink),
        SizedBox(width: space.s),
        Text(title, style: type.titleS.copyWith(color: colors.ink)),
        SizedBox(width: space.s),
        if (count > 0)
          Container(
            padding: context.fuzzzyDensity.chip,
            decoration: BoxDecoration(
              // A count badge is a discrete marker, so it takes the action
              // pair — the fork's gold-at-alpha-0.15 pill is the tinted-panel
              // row USING §2.4 forbids.
              color: colors.actionPrimaryBg,
              borderRadius: BorderRadius.circular(radius.s),
            ),
            // A bare integer is Latin-only, so it can take the mono `dataS`.
            child: Text(
              '$count',
              style: type.dataS.copyWith(color: colors.actionPrimaryFg),
            ),
          ),
      ],
    );
  }
}

class _ClarificationTile extends StatelessWidget {
  const _ClarificationTile({
    required this.item,
    required this.onToggle,
    required this.onDelete,
  });
  final ClarificationData item;
  final VoidCallback onToggle;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;

    // Both states are ONE box now. The fork gave the open state a
    // warning-tinted panel and the resolved state a half-alpha panel — two
    // alpha tints doing what a rule and a strikethrough already say.
    //
    // The open state keeps its `warning` voice, as a 3px left rule
    // (FuzzzyBanner's shape); resolved drops back to the plain hairline.
    // T-0254: as a per-side `Border` + `borderRadius` this threw at paint in
    // the UNRESOLVED state only (resolved had one distinct visible colour and
    // painted fine) — a state-dependent throw a resolved-only screenshot misses.
    return Padding(
      padding: EdgeInsets.only(bottom: space.s),
      child: AppRuleCard(
        rule: item.isResolved ? colors.line : colors.warning,
        ruleWidth: 3,
        borderRadius: radius.m,
        padding: context.fuzzzyDensity.tile,
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            FuzzzyHitTarget(
              child: GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTap: onToggle,
                child: Padding(
                  padding: EdgeInsets.only(top: space.xs),
                  child: Icon(
                    item.isResolved
                        ? Icons.check_circle
                        : Icons.radio_button_unchecked,
                    size: 22,
                    color: item.isResolved ? colors.success : colors.warning,
                  ),
                ),
              ),
            ),
            SizedBox(width: space.m),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.question,
                    style: type.body.copyWith(
                      color: item.isResolved ? colors.inkMute : colors.ink,
                      decoration: item.isResolved
                          ? TextDecoration.lineThrough
                          : null,
                      decorationColor: colors.inkMute,
                    ),
                  ),
                  if (item.resolution != null &&
                      item.resolution!.isNotEmpty) ...[
                    SizedBox(height: space.xs),
                    Text(
                      '→ ${item.resolution}',
                      style: type.bodyS.copyWith(color: colors.success),
                    ),
                  ],
                ],
              ),
            ),
            FuzzzyHitTarget(
              child: GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTap: onDelete,
                // Alpha 0.5 deleted: `inkFaint` IS the de-emphasised rung.
                child: Icon(Icons.close, size: 16, color: colors.inkFaint),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ActionItemTile extends StatelessWidget {
  const _ActionItemTile({
    required this.item,
    required this.onToggle,
    required this.onDelete,
    required this.onEdit,
  });
  final ActionItemData item;
  final VoidCallback onToggle;
  final VoidCallback onDelete;
  final ValueChanged<String> onEdit;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;

    return Container(
      margin: EdgeInsets.only(bottom: space.s),
      padding: context.fuzzzyDensity.tile,
      decoration: BoxDecoration(
        color: colors.surface,
        borderRadius: BorderRadius.circular(radius.m),
        border: Border.all(color: colors.line),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          FuzzzyHitTarget(
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: onToggle,
              child: Padding(
                padding: EdgeInsets.only(top: space.xs),
                child: Icon(
                  item.isCompleted
                      ? Icons.check_circle
                      : Icons.radio_button_unchecked,
                  size: 22,
                  // Done keeps `success`; the OPEN state is `ink`, not a
                  // semantic role — an unticked checkbox is not a status.
                  color: item.isCompleted ? colors.success : colors.ink,
                ),
              ),
            ),
          ),
          SizedBox(width: space.m),
          Expanded(
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onDoubleTap: () => _showEditDialog(context),
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
          ),
          if (item.deadline != null) ...[
            SizedBox(width: space.s),
            Text(
              _formatDeadline(item.deadline!),
              // A deadline countdown is meta. It carries Georgian, so it is
              // `bodyS`, never the mono `dataS` (JOURNAL M6b judgement 4).
              style: type.bodyS.copyWith(color: colors.inkFaint),
            ),
          ],
          SizedBox(width: space.s),
          FuzzzyHitTarget(
            child: GestureDetector(
              behavior: HitTestBehavior.opaque,
              onTap: onDelete,
              child: Icon(Icons.close, size: 16, color: colors.inkFaint),
            ),
          ),
        ],
      ),
    );
  }

  String _formatDeadline(DateTime date) {
    final diff = date.difference(DateTime.now()).inDays;
    if (diff < 0) return '${-diff}დ. გადაცილ.';
    if (diff == 0) return 'დღეს';
    if (diff == 1) return 'ხვალ';
    return '$diffდ.';
  }

  void _showEditDialog(BuildContext context) {
    final controller = TextEditingController(text: item.task);
    showDialog<void>(
      context: context,
      builder: (ctx) {
        final colors = ctx.fuzzzyColors;
        final type = ctx.fuzzzyTextStyles;
        final radius = ctx.fuzzzyRadius;
        return AlertDialog(
          backgroundColor: colors.raised,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(radius.l),
            side: BorderSide(color: colors.lineStrong),
          ),
          title: Text(
            'რედაქტირება',
            style: type.titleS.copyWith(color: colors.ink),
          ),
          content: TextField(
            controller: controller,
            autofocus: true,
            maxLines: 3,
            style: type.body.copyWith(color: colors.fieldText),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: Text(
                'გაუქმება',
                style: type.control.copyWith(color: colors.inkMute),
              ),
            ),
            TextButton(
              onPressed: () {
                onEdit(controller.text.trim());
                Navigator.pop(ctx);
              },
              child: Text(
                'შენახვა',
                style: type.control.copyWith(color: colors.ink),
              ),
            ),
          ],
        );
      },
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.text});
  final String text;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    return Container(
      padding: context.fuzzzyDensity.screen,
      alignment: Alignment.center,
      child: Text(
        text,
        style: context.fuzzzyTextStyles.body.copyWith(color: colors.inkMute),
      ),
    );
  }
}
