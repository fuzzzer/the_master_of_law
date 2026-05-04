import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

/// Bottom sheet for creating a new case.
/// Title input + domain picker grid → "შექმნა" button.
class NewCaseSheet extends StatefulWidget {
  const NewCaseSheet({super.key});

  @override
  State<NewCaseSheet> createState() => _NewCaseSheetState();
}

class _NewCaseSheetState extends State<NewCaseSheet> {
  final _titleController = TextEditingController();
  LegalDomain _selectedDomain = LegalDomain.civil;
  bool _isCreating = false;

  @override
  void dispose() {
    _titleController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Padding(
      padding: EdgeInsets.only(
        left: 20,
        right: 20,
        top: 20,
        bottom: MediaQuery.of(context).viewInsets.bottom + 20,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Handle bar
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: uiColors.secondaryTextColor.withValues(alpha: 0.3),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 20),
          // Title
          Text(
            'ახალი საქმე',
            style: uiTextStyles.headlineBold20.copyWith(
              color: uiColors.primaryTextColor,
            ),
          ),
          const SizedBox(height: 20),
          // Case title field
          Text(
            'სათაური:',
            style: uiTextStyles.bodyBold14.copyWith(
              color: uiColors.secondaryTextColor,
            ),
          ),
          const SizedBox(height: 8),
          TextField(
            controller: _titleController,
            style: uiTextStyles.body16.copyWith(color: uiColors.primaryTextColor),
            decoration: InputDecoration(
              hintText: 'მაგ: მემამულის დავა',
              hintStyle: uiTextStyles.body16.copyWith(
                color: uiColors.secondaryTextColor.withValues(alpha: 0.5),
              ),
            ),
          ),
          const SizedBox(height: 20),
          // Domain picker
          Text(
            'სფერო:',
            style: uiTextStyles.bodyBold14.copyWith(
              color: uiColors.secondaryTextColor,
            ),
          ),
          const SizedBox(height: 12),
          _DomainPickerGrid(
            selectedDomain: _selectedDomain,
            onDomainSelected: (domain) {
              setState(() => _selectedDomain = domain);
            },
          ),
          const SizedBox(height: 24),
          // Create button
          SizedBox(
            width: double.infinity,
            height: 52,
            child: ElevatedButton(
              onPressed: _isCreating ? null : _createCase,
              style: ElevatedButton.styleFrom(
                backgroundColor: uiColors.accentColor,
                foregroundColor: uiColors.backgroundPrimaryColor,
                disabledBackgroundColor: uiColors.accentColor.withValues(alpha: 0.5),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                textStyle: uiTextStyles.bodyBold16,
              ),
              child: _isCreating
                  ? SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: uiColors.backgroundPrimaryColor,
                      ),
                    )
                  : const Text('შექმნა და დაწყება →'),
            ),
          ),
        ],
      ),
    );
  }

  Future<void> _createCase() async {
    final title = _titleController.text.trim();
    if (title.isEmpty) return;

    setState(() => _isCreating = true);

    final caseData = await context.read<CasesCubit>().createCase(
      title: title,
      domain: _selectedDomain,
    );

    if (!mounted) return;
    Navigator.pop(context);

    if (caseData != null) {
      CaseWorkspacePage.navigate(context, caseData.id);
    }
  }
}

class _DomainPickerGrid extends StatelessWidget {
  const _DomainPickerGrid({
    required this.selectedDomain,
    required this.onDomainSelected,
  });

  final LegalDomain selectedDomain;
  final ValueChanged<LegalDomain> onDomainSelected;

  Color _domainColor(LegalDomain domain, UiColors uiColors) => switch (domain) {
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

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: LegalDomain.values.map((domain) {
        final isSelected = domain == selectedDomain;
        final color = _domainColor(domain, uiColors);

        return GestureDetector(
          onTap: () => onDomainSelected(domain),
          child: AnimatedContainer(
            duration: const Duration(milliseconds: 200),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: BoxDecoration(
              color: isSelected ? color.withValues(alpha: 0.2) : Colors.transparent,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(
                color: isSelected ? color : uiColors.secondaryTextColor.withValues(alpha: 0.2),
                width: isSelected ? 2 : 1,
              ),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: color,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 6),
                Text(
                  domain.shortLabelKa,
                  style: uiTextStyles.labelBold12.copyWith(
                    color: isSelected ? color : uiColors.secondaryTextColor,
                  ),
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }
}
