import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

/// Facts management with three-segment categorization: Favorable/Unfavorable/Neutral.
class CaseFactsSection extends StatefulWidget {
  const CaseFactsSection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  State<CaseFactsSection> createState() => _CaseFactsSectionState();
}

class _CaseFactsSectionState extends State<CaseFactsSection> {
  late FactClassification _selectedFilter = _initialFilter();

  FactClassification _initialFilter() {
    for (final fc in FactClassification.values) {
      if (widget.caseData.facts.any((f) => f.classificationIndex == fc.index)) {
        return fc;
      }
    }
    return FactClassification.favorable;
  }

  List<FactData> get _filteredFacts =>
      widget.caseData.facts.where((f) => f.classificationIndex == _selectedFilter.index).toList();

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Column(
      children: [
        // Segment control
        Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: FactClassification.values.map((fc) {
              final count = widget.caseData.facts.where((f) => f.classificationIndex == fc.index).length;
              final isSelected = fc == _selectedFilter;
              final color = switch (fc) {
                FactClassification.favorable => uiColors.successColor,
                FactClassification.unfavorable => uiColors.errorColor,
                FactClassification.neutral => uiColors.infoColor,
              };
              return Expanded(
                child: GestureDetector(
                  onTap: () => setState(() => _selectedFilter = fc),
                  child: AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    padding: const EdgeInsets.symmetric(vertical: 10),
                    decoration: BoxDecoration(
                      color: isSelected ? color.withValues(alpha: 0.15) : Colors.transparent,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(
                        color: isSelected ? color : Colors.transparent,
                      ),
                    ),
                    child: Column(
                      children: [
                        Text(fc.emoji, style: const TextStyle(fontSize: 18)),
                        const SizedBox(height: 4),
                        Text(
                          '${fc.displayNameKa} ($count)',
                          style: uiTextStyles.labelBold12.copyWith(
                            color: isSelected ? color : uiColors.secondaryTextColor,
                          ),
                          textAlign: TextAlign.center,
                        ),
                      ],
                    ),
                  ),
                ),
              );
            }).toList(),
          ),
        ),

        // Facts list
        Expanded(
          child: _filteredFacts.isEmpty
              ? Center(
                  child: Text(
                    'ჯერ არ არის ${_selectedFilter.displayNameKa} ფაქტი',
                    style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                  ),
                )
              : ListView.separated(
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: _filteredFacts.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (context, index) {
                    final fact = _filteredFacts[index];
                    final accentColor = switch (fact.classification) {
                      FactClassification.favorable => uiColors.successColor,
                      FactClassification.unfavorable => uiColors.errorColor,
                      FactClassification.neutral => uiColors.infoColor,
                    };
                    return Dismissible(
                      key: ValueKey(fact.id),
                      direction: DismissDirection.endToStart,
                      onDismissed: (_) => context.read<CaseDetailCubit>().deleteFact(fact.id),
                      background: Container(
                        alignment: Alignment.centerRight,
                        padding: const EdgeInsets.only(right: 16),
                        child: Icon(Icons.delete, color: uiColors.errorColor),
                      ),
                      child: Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: uiColors.backgroundSecondaryColor,
                          borderRadius: BorderRadius.circular(10),
                          border: Border(left: BorderSide(color: accentColor, width: 4)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              fact.text,
                              style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
                            ),
                            if (fact.isAiGenerated) ...[
                              const SizedBox(height: 6),
                              Row(
                                children: [
                                  Icon(Icons.psychology, size: 14, color: uiColors.accentColor),
                                  const SizedBox(width: 4),
                                  Text(
                                    'AI-ით ამოცნობილი',
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

        // Add fact button
        Padding(
          padding: const EdgeInsets.all(16),
          child: SizedBox(
            width: double.infinity,
            child: OutlinedButton.icon(
              onPressed: () => _showAddFactDialog(context),
              icon: const Icon(Icons.add),
              label: const Text('დაამატეთ ფაქტი'),
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

  void _showAddFactDialog(BuildContext context) {
    final controller = TextEditingController();
    var classification = _selectedFilter;
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: uiColors.backgroundSecondaryColor,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (sheetContext) {
        return StatefulBuilder(
          builder: (ctx, setSheetState) {
            return Padding(
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
                  Text('ახალი ფაქტი', style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor)),
                  const SizedBox(height: 16),
                  TextField(
                    controller: controller,
                    maxLines: 3,
                    style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
                    decoration: InputDecoration(
                      hintText: 'აღწერეთ ფაქტი...',
                      hintStyle: uiTextStyles.body14.copyWith(
                        color: uiColors.secondaryTextColor.withValues(alpha: 0.5),
                      ),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: FactClassification.values.map((fc) {
                      final isSelected = fc == classification;
                      return Expanded(
                        child: GestureDetector(
                          onTap: () => setSheetState(() => classification = fc),
                          child: Container(
                            padding: const EdgeInsets.symmetric(vertical: 8),
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
                              '${fc.emoji} ${fc.displayNameKa}',
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
                        if (controller.text.trim().isEmpty) return;
                        final fact = FactData(
                          id: DateTime.now().millisecondsSinceEpoch.toString(),
                          text: controller.text.trim(),
                          classificationIndex: classification.index,
                          createdAt: DateTime.now(),
                        );
                        context.read<CaseDetailCubit>().addFact(fact);
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
            );
          },
        );
      },
    );
  }
}
