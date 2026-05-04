import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

/// Risks + weaknesses: severity badges, mitigation, "Red Team" button.
class CaseRisksSection extends StatelessWidget {
  const CaseRisksSection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Column(
      children: [
        Expanded(
          child: caseData.risks.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.warning_amber, size: 48, color: uiColors.warningColor.withValues(alpha: 0.5)),
                      const SizedBox(height: 16),
                      Text(
                        'რისკები ჯერ არ არის',
                        style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'სუსტი მხარეების გამოვლენა\nგეხმარებათ უკეთეს მომზადებაში',
                        style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
                        textAlign: TextAlign.center,
                      ),
                    ],
                  ),
                )
              : ListView.separated(
                  padding: const EdgeInsets.all(16),
                  itemCount: caseData.risks.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 10),
                  itemBuilder: (context, index) {
                    final risk = caseData.risks[index];
                    final severityColor = switch (risk.severity) {
                      RiskSeverity.high => uiColors.errorColor,
                      RiskSeverity.medium => uiColors.warningColor,
                      RiskSeverity.low => uiColors.infoColor,
                    };
                    return Dismissible(
                      key: ValueKey(risk.id),
                      direction: DismissDirection.endToStart,
                      onDismissed: (_) => context.read<CaseDetailCubit>().deleteRisk(risk.id),
                      background: Container(
                        alignment: Alignment.centerRight,
                        padding: const EdgeInsets.only(right: 16),
                        child: Icon(Icons.delete, color: uiColors.errorColor),
                      ),
                      child: Container(
                        padding: const EdgeInsets.all(14),
                        decoration: BoxDecoration(
                          color: uiColors.backgroundSecondaryColor,
                          borderRadius: BorderRadius.circular(12),
                          border: Border(left: BorderSide(color: severityColor, width: 4)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Expanded(
                                  child: Text(
                                    risk.description,
                                    style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    color: severityColor.withValues(alpha: 0.15),
                                    borderRadius: BorderRadius.circular(6),
                                  ),
                                  child: Text(
                                    risk.severity.displayNameKa,
                                    style: uiTextStyles.labelBold12.copyWith(color: severityColor),
                                  ),
                                ),
                              ],
                            ),
                            if (risk.mitigationSuggestion != null && risk.mitigationSuggestion!.isNotEmpty) ...[
                              const SizedBox(height: 8),
                              Row(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Icon(Icons.lightbulb_outline, size: 16, color: uiColors.accentColor),
                                  const SizedBox(width: 6),
                                  Expanded(
                                    child: Text(
                                      risk.mitigationSuggestion!,
                                      style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                                    ),
                                  ),
                                ],
                              ),
                            ],
                            if (risk.isAiGenerated) ...[
                              const SizedBox(height: 6),
                              Row(
                                children: [
                                  Icon(Icons.psychology, size: 14, color: uiColors.accentColor),
                                  const SizedBox(width: 4),
                                  Text(
                                    'AI-ის მიერ გენერირებული',
                                    style: uiTextStyles.caption11.copyWith(color: uiColors.accentColor),
                                  ),
                                ],
                              ),
                            ],
                          ],
                        ),
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
              onPressed: () => _showAddRisk(context),
              icon: const Icon(Icons.add),
              label: const Text('რისკის დამატება'),
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

  void _showAddRisk(BuildContext parentContext) {
    final descController = TextEditingController();
    final mitigationController = TextEditingController();
    var severity = RiskSeverity.medium;
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
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('ახალი რისკი', style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor)),
                const SizedBox(height: 16),
                TextField(
                  controller: descController,
                  maxLines: 3,
                  style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
                  decoration: InputDecoration(
                    hintText: 'აღწერეთ რისკი...',
                    hintStyle: uiTextStyles.body14.copyWith(
                      color: uiColors.secondaryTextColor.withValues(alpha: 0.5),
                    ),
                  ),
                ),
                const SizedBox(height: 12),
                Text('სიმძიმე:', style: uiTextStyles.bodyBold14.copyWith(color: uiColors.secondaryTextColor)),
                const SizedBox(height: 8),
                Row(
                  children: RiskSeverity.values.map((s) {
                    final isSelected = s == severity;
                    final color = switch (s) {
                      RiskSeverity.high => uiColors.errorColor,
                      RiskSeverity.medium => uiColors.warningColor,
                      RiskSeverity.low => uiColors.infoColor,
                    };
                    return Expanded(
                      child: GestureDetector(
                        onTap: () => setState(() => severity = s),
                        child: Container(
                          padding: const EdgeInsets.symmetric(vertical: 10),
                          margin: const EdgeInsets.symmetric(horizontal: 4),
                          decoration: BoxDecoration(
                            color: isSelected ? color.withValues(alpha: 0.2) : Colors.transparent,
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: isSelected ? color : uiColors.secondaryTextColor.withValues(alpha: 0.2),
                            ),
                          ),
                          child: Text(
                            s.displayNameKa,
                            textAlign: TextAlign.center,
                            style: uiTextStyles.labelBold12.copyWith(
                              color: isSelected ? color : uiColors.secondaryTextColor,
                            ),
                          ),
                        ),
                      ),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: mitigationController,
                  maxLines: 2,
                  style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
                  decoration: InputDecoration(
                    hintText: 'შემარბილებელი ზომა (არასავალდებულო)...',
                    hintStyle: uiTextStyles.body14.copyWith(
                      color: uiColors.secondaryTextColor.withValues(alpha: 0.5),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  height: 48,
                  child: ElevatedButton(
                    onPressed: () {
                      if (descController.text.trim().isEmpty) return;
                      parentContext.read<CaseDetailCubit>().addRisk(
                        RiskData(
                          id: DateTime.now().millisecondsSinceEpoch.toString(),
                          description: descController.text.trim(),
                          severityIndex: severity.index,
                          mitigationSuggestion: mitigationController.text.trim().isEmpty
                              ? null
                              : mitigationController.text.trim(),
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
      ),
    );
  }
}
