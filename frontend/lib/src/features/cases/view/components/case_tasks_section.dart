import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

/// Combined tasks + clarifications section for the case workspace.
class CaseTasksSection extends StatelessWidget {
  const CaseTasksSection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final cubit = context.read<CaseDetailCubit>();

    return BlocBuilder<CaseDetailCubit, CaseDetailState>(
      builder: (context, state) {
        final data = state.caseData ?? caseData;

        return ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // ── Clarifications ──
            if (data.clarifications.isNotEmpty) ...[
              _SectionHeader(
                icon: Icons.help_outline,
                title: 'დასაზუსტებელი ინფორმაცია',
                count: data.clarifications.where((c) => !c.isResolved).length,
                uiColors: uiColors,
                uiTextStyles: uiTextStyles,
              ),
              const SizedBox(height: 8),
              ...data.clarifications.map(
                (item) => _ClarificationTile(
                  item: item,
                  uiColors: uiColors,
                  uiTextStyles: uiTextStyles,
                  onToggle: () => cubit.toggleClarification(item.id),
                  onDelete: () => cubit.deleteClarification(item.id),
                ),
              ),
              const SizedBox(height: 24),
            ],

            // ── Action Items (Tasks) ──
            _SectionHeader(
              icon: Icons.checklist,
              title: 'დავალებები',
              count: data.actionItems.where((i) => !i.isCompleted).length,
              uiColors: uiColors,
              uiTextStyles: uiTextStyles,
            ),
            const SizedBox(height: 8),
            if (data.actionItems.isEmpty)
              _EmptyState(
                text: 'დავალებები ჯერ არ არის',
                uiColors: uiColors,
                uiTextStyles: uiTextStyles,
              ),
            ...data.actionItems.map(
              (item) => _ActionItemTile(
                item: item,
                uiColors: uiColors,
                uiTextStyles: uiTextStyles,
                onToggle: () => cubit.toggleActionItem(item.id),
                onDelete: () => cubit.deleteActionItem(item.id),
                onEdit: (newText) {
                  item.task = newText;
                  cubit.updateActionItemText(item.id, newText);
                },
              ),
            ),
            const SizedBox(height: 16),

            // ── Add Task Button ──
            OutlinedButton.icon(
              onPressed: () => _showAddTaskDialog(context, cubit, uiColors, uiTextStyles),
              icon: const Icon(Icons.add, size: 18),
              label: const Text('დავალების დამატება'),
              style: OutlinedButton.styleFrom(
                foregroundColor: uiColors.accentColor,
                side: BorderSide(color: uiColors.accentColor.withValues(alpha: 0.3)),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                padding: const EdgeInsets.symmetric(vertical: 14),
              ),
            ),
          ],
        );
      },
    );
  }

  void _showAddTaskDialog(BuildContext context, CaseDetailCubit cubit, UiColors uiColors, UiTextStyles uiTextStyles) {
    final controller = TextEditingController();
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: uiColors.backgroundPrimaryColor,
        title: Text('ახალი დავალება', style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor)),
        content: TextField(
          controller: controller,
          autofocus: true,
          maxLines: 3,
          style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
          decoration: InputDecoration(
            hintText: 'რა უნდა გაკეთდეს...',
            hintStyle: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: Text('გაუქმება', style: TextStyle(color: uiColors.secondaryTextColor)),
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
            child: Text('დამატება', style: TextStyle(color: uiColors.accentColor)),
          ),
        ],
      ),
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({
    required this.icon,
    required this.title,
    required this.count,
    required this.uiColors,
    required this.uiTextStyles,
  });
  final IconData icon;
  final String title;
  final int count;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 20, color: uiColors.accentColor),
        const SizedBox(width: 8),
        Text(title, style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor)),
        const SizedBox(width: 8),
        if (count > 0)
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: uiColors.accentColor.withValues(alpha: 0.15),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Text('$count', style: uiTextStyles.labelBold12.copyWith(color: uiColors.accentColor)),
          ),
      ],
    );
  }
}

class _ClarificationTile extends StatelessWidget {
  const _ClarificationTile({
    required this.item,
    required this.uiColors,
    required this.uiTextStyles,
    required this.onToggle,
    required this.onDelete,
  });
  final ClarificationData item;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;
  final VoidCallback onToggle;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: item.isResolved
            ? uiColors.backgroundSecondaryColor.withValues(alpha: 0.5)
            : uiColors.warningColor.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: item.isResolved
              ? uiColors.secondaryTextColor.withValues(alpha: 0.1)
              : uiColors.warningColor.withValues(alpha: 0.2),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GestureDetector(
            onTap: onToggle,
            child: Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Icon(
                item.isResolved ? Icons.check_circle : Icons.radio_button_unchecked,
                size: 22,
                color: item.isResolved ? uiColors.successColor : uiColors.warningColor,
              ),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  item.question,
                  style: uiTextStyles.body14.copyWith(
                    color: item.isResolved ? uiColors.secondaryTextColor : uiColors.primaryTextColor,
                    decoration: item.isResolved ? TextDecoration.lineThrough : null,
                  ),
                ),
                if (item.resolution != null && item.resolution!.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    '→ ${item.resolution}',
                    style: uiTextStyles.label12.copyWith(color: uiColors.successColor),
                  ),
                ],
              ],
            ),
          ),
          GestureDetector(
            onTap: onDelete,
            child: Icon(Icons.close, size: 16, color: uiColors.secondaryTextColor.withValues(alpha: 0.5)),
          ),
        ],
      ),
    );
  }
}

class _ActionItemTile extends StatelessWidget {
  const _ActionItemTile({
    required this.item,
    required this.uiColors,
    required this.uiTextStyles,
    required this.onToggle,
    required this.onDelete,
    required this.onEdit,
  });
  final ActionItemData item;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;
  final VoidCallback onToggle;
  final VoidCallback onDelete;
  final ValueChanged<String> onEdit;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: uiColors.backgroundSecondaryColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: uiColors.secondaryTextColor.withValues(alpha: 0.1)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          GestureDetector(
            onTap: onToggle,
            child: Padding(
              padding: const EdgeInsets.only(top: 2),
              child: Icon(
                item.isCompleted ? Icons.check_circle : Icons.radio_button_unchecked,
                size: 22,
                color: item.isCompleted ? uiColors.successColor : uiColors.accentColor,
              ),
            ),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: GestureDetector(
              onDoubleTap: () => _showEditDialog(context),
              child: Text(
                item.task,
                style: uiTextStyles.body14.copyWith(
                  color: item.isCompleted ? uiColors.secondaryTextColor : uiColors.primaryTextColor,
                  decoration: item.isCompleted ? TextDecoration.lineThrough : null,
                ),
              ),
            ),
          ),
          if (item.deadline != null) ...[
            const SizedBox(width: 8),
            Text(
              _formatDeadline(item.deadline!),
              style: uiTextStyles.label12.copyWith(color: uiColors.secondaryTextColor),
            ),
          ],
          const SizedBox(width: 8),
          GestureDetector(
            onTap: onDelete,
            child: Icon(Icons.close, size: 16, color: uiColors.secondaryTextColor.withValues(alpha: 0.5)),
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
    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('რედაქტირება'),
        content: TextField(controller: controller, autofocus: true, maxLines: 3),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('გაუქმება')),
          TextButton(
            onPressed: () {
              onEdit(controller.text.trim());
              Navigator.pop(ctx);
            },
            child: const Text('შენახვა'),
          ),
        ],
      ),
    );
  }
}

class _EmptyState extends StatelessWidget {
  const _EmptyState({required this.text, required this.uiColors, required this.uiTextStyles});
  final String text;
  final UiColors uiColors;
  final UiTextStyles uiTextStyles;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      alignment: Alignment.center,
      child: Text(text, style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor)),
    );
  }
}
