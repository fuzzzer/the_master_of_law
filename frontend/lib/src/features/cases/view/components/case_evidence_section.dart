import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

/// Evidence management: grid/list of attached items with add button.
class CaseEvidenceSection extends StatelessWidget {
  const CaseEvidenceSection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Column(
      children: [
        Expanded(
          child: caseData.evidence.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.attach_file, size: 48, color: uiColors.accentColor.withValues(alpha: 0.5)),
                      const SizedBox(height: 16),
                      Text(
                        'ჯერ არ არის მტკიცებულება',
                        style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                      ),
                    ],
                  ),
                )
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: caseData.evidence.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final ev = caseData.evidence[index];
                    final icon = switch (ev.type) {
                      EvidenceType.document => Icons.description,
                      EvidenceType.photo => Icons.photo,
                      EvidenceType.screenshot => Icons.screenshot,
                      EvidenceType.receipt => Icons.receipt,
                      EvidenceType.other => Icons.attachment,
                    };
                    return Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: uiColors.backgroundSecondaryColor,
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Row(
                        children: [
                          Icon(icon, color: uiColors.accentColor, size: 28),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  ev.title,
                                  style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
                                ),
                                Text(
                                  ev.type.displayNameKa,
                                  style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                                ),
                              ],
                            ),
                          ),
                          IconButton(
                            icon: Icon(Icons.delete_outline, color: uiColors.errorColor, size: 20),
                            onPressed: () => context.read<CaseDetailCubit>().deleteEvidence(ev.id),
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
              onPressed: () => _showAddEvidence(context),
              icon: const Icon(Icons.add),
              label: const Text('📎 დაამატეთ'),
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

  void _showAddEvidence(BuildContext parentContext) {
    final cubit = parentContext.read<CaseDetailCubit>();
    final controller = TextEditingController();
    var selectedType = EvidenceType.document;
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
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('ახალი მტკიცებულება', style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor)),
              const SizedBox(height: 16),
              TextField(
                controller: controller,
                style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
                decoration: InputDecoration(
                  hintText: 'სათაური...',
                  hintStyle: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor.withValues(alpha: 0.5)),
                ),
              ),
              const SizedBox(height: 12),
              Wrap(
                spacing: 8,
                children: EvidenceType.values.map((t) {
                  final isSelected = t == selectedType;
                  return ChoiceChip(
                    label: Text(t.displayNameKa),
                    selected: isSelected,
                    selectedColor: uiColors.accentColor.withValues(alpha: 0.2),
                    labelStyle: uiTextStyles.labelBold12.copyWith(
                      color: isSelected ? uiColors.accentColor : uiColors.secondaryTextColor,
                    ),
                    onSelected: (_) => setState(() => selectedType = t),
                  );
                }).toList(),
              ),
              const SizedBox(height: 20),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton(
                  onPressed: () async {
                    if (controller.text.trim().isEmpty) return;
                    await cubit.addEvidence(
                      EvidenceData(
                        id: DateTime.now().millisecondsSinceEpoch.toString(),
                        title: controller.text.trim(),
                        typeIndex: selectedType.index,
                        addedAt: DateTime.now(),
                      ),
                    );
                    if (ctx.mounted) Navigator.pop(ctx);
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
