import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

/// Timeline + deadlines with vertical visualization, countdown display, urgency colors.
class CaseTimelineSection extends StatelessWidget {
  const CaseTimelineSection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final events = List<TimelineEventData>.from(caseData.timeline)..sort((a, b) => a.date.compareTo(b.date));

    return Column(
      children: [
        Expanded(
          child: events.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.timeline, size: 48, color: uiColors.accentColor.withValues(alpha: 0.5)),
                      const SizedBox(height: 16),
                      Text(
                        'ვადები ჯერ არ არის',
                        style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                      ),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: events.length,
                  itemBuilder: (context, index) {
                    final event = events[index];
                    final isLast = index == events.length - 1;
                    final typeColor = switch (event.type) {
                      TimelineEventType.past => uiColors.successColor,
                      TimelineEventType.deadline =>
                        event.daysRemaining < 7
                            ? uiColors.errorColor
                            : event.daysRemaining < 30
                            ? uiColors.warningColor
                            : uiColors.successColor,
                      TimelineEventType.milestone => uiColors.accentColor,
                    };

                    return IntrinsicHeight(
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          SizedBox(
                            width: 32,
                            child: Column(
                              children: [
                                Container(
                                  width: 12,
                                  height: 12,
                                  decoration: BoxDecoration(color: typeColor, shape: BoxShape.circle),
                                ),
                                if (!isLast) Expanded(child: Container(width: 2, color: uiColors.surfaceColor)),
                              ],
                            ),
                          ),
                          Expanded(
                            child: Padding(
                              padding: const EdgeInsets.only(bottom: 20),
                              child: Container(
                                padding: const EdgeInsets.all(12),
                                decoration: BoxDecoration(
                                  color: uiColors.backgroundSecondaryColor,
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border(left: BorderSide(color: typeColor, width: 3)),
                                ),
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Row(
                                      children: [
                                        Text(event.type.icon, style: const TextStyle(fontSize: 16)),
                                        const SizedBox(width: 8),
                                        Expanded(
                                          child: Text(
                                            event.title,
                                            style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
                                          ),
                                        ),
                                        if (event.type == TimelineEventType.deadline)
                                          Text(
                                            event.daysRemaining > 0
                                                ? '${event.daysRemaining} დღე'
                                                : event.daysRemaining == 0
                                                ? 'დღეს!'
                                                : 'ვადაგადაც.',
                                            style: uiTextStyles.labelBold12.copyWith(color: typeColor),
                                          ),
                                      ],
                                    ),
                                    const SizedBox(height: 4),
                                    Text(
                                      '${event.date.day}.${event.date.month.toString().padLeft(2, '0')}.${event.date.year}',
                                      style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                                    ),
                                    if (event.description != null && event.description!.isNotEmpty) ...[
                                      const SizedBox(height: 6),
                                      Text(
                                        event.description!,
                                        style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                                      ),
                                    ],
                                  ],
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => _showAddEvent(context),
              icon: const Icon(Icons.add),
              label: const Text('ახალი ვადა'),
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

  void _showAddEvent(BuildContext parentContext) {
    final titleController = TextEditingController();
    var selectedDate = DateTime.now().add(const Duration(days: 7));
    var selectedType = TimelineEventType.deadline;
    final uiColors = parentContext.uiColors;
    final uiTextStyles = parentContext.uiTextStyles;

    showModalBottomSheet<void>(
      context: parentContext,
      isScrollControlled: true,
      backgroundColor: uiColors.backgroundSecondaryColor,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setState) => Padding(
          padding: EdgeInsets.only(
            left: 20,
            right: 20,
            top: 20,
            bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'ახალი მოვლენა',
                style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: titleController,
                style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
                decoration: const InputDecoration(hintText: 'სათაური...'),
              ),
              const SizedBox(height: 12),
              GestureDetector(
                onTap: () async {
                  final picked = await showDatePicker(
                    context: ctx,
                    initialDate: selectedDate,
                    firstDate: DateTime(2020),
                    lastDate: DateTime(2030),
                  );
                  if (picked != null) setState(() => selectedDate = picked);
                },
                child: Container(
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: uiColors.surfaceColor,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.calendar_today, size: 20, color: uiColors.accentColor),
                      const SizedBox(width: 8),
                      Text(
                        '${selectedDate.day}.${selectedDate.month.toString().padLeft(2, '0')}.${selectedDate.year}',
                        style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Row(
                children: TimelineEventType.values.map((t) {
                  final isSelected = t == selectedType;
                  return Expanded(
                    child: GestureDetector(
                      onTap: () => setState(() => selectedType = t),
                      child: Container(
                        padding: const EdgeInsets.symmetric(vertical: 10),
                        margin: const EdgeInsets.symmetric(horizontal: 4),
                        decoration: BoxDecoration(
                          color: isSelected ? uiColors.accentColor.withValues(alpha: 0.2) : Colors.transparent,
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                            color: isSelected
                                ? uiColors.accentColor
                                : uiColors.secondaryTextColor.withValues(alpha: 0.2),
                          ),
                        ),
                        child: Text(
                          '${t.icon} ${t.displayNameKa}',
                          textAlign: TextAlign.center,
                          style: uiTextStyles.labelBold12.copyWith(
                            color: isSelected ? uiColors.accentColor : uiColors.secondaryTextColor,
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: () {
                    if (titleController.text.trim().isEmpty) return;
                    parentContext.read<CaseDetailCubit>().addTimelineEvent(
                      TimelineEventData(
                        id: DateTime.now().millisecondsSinceEpoch.toString(),
                        date: selectedDate,
                        title: titleController.text.trim(),
                        typeIndex: selectedType.index,
                      ),
                    );
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
      ),
    );
  }
}
