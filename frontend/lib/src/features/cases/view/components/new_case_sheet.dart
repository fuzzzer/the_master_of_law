import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:themasteroflaw/src/src.dart';

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
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return Container(
      decoration: BoxDecoration(
        // Rung 2 of the ladder: an overlay is `raised` + `lineStrong`
        // (M5's feedback_sheet idiom, copied exactly).
        color: colors.raised,
        border: Border(top: BorderSide(color: colors.lineStrong)),
        borderRadius: BorderRadius.vertical(top: Radius.circular(radius.l)),
      ),
      padding: density.dialog.copyWith(
        bottom: density.dialog.bottom + MediaQuery.of(context).viewInsets.bottom,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Handle bar
          Center(
            child: Container(
              // Dimensions, not gaps: the grabber's fixed footprint.
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                // `lineStrong`, not `line`: on a `raised` sheet a `line`
                // hairline all but disappears, and a grabber is an affordance.
                color: colors.lineStrong,
                borderRadius: BorderRadius.circular(radius.s),
              ),
            ),
          ),
          SizedBox(height: space.l),
          // Title
          Text('ახალი საქმე', style: type.titleM.copyWith(color: colors.ink)),
          SizedBox(height: space.l),
          // Case title field
          Text(
            'სათაური:',
            // A Georgian section label above an input is `control` + `ink`,
            // NOT `fieldLabel` — that role paints an InputDecoration's own
            // floating label (JOURNAL M6 §G).
            style: type.control.copyWith(color: colors.ink),
          ),
          SizedBox(height: space.s),
          TextField(
            controller: _titleController,
            style: type.body.copyWith(color: colors.fieldText),
            // Fill, all five border states, radius, content padding and the
            // hint style all come from M1's inputDecorationTheme.
            decoration: const InputDecoration(hintText: 'მაგ: მემამულის დავა'),
          ),
          SizedBox(height: space.l),
          // Domain picker
          Text(
            'სფერო:',
            style: type.control.copyWith(color: colors.ink),
          ),
          SizedBox(height: space.m),
          _DomainPickerGrid(
            selectedDomain: _selectedDomain,
            onDomainSelected: (domain) {
              setState(() => _selectedDomain = domain);
            },
          ),
          SizedBox(height: space.xl),
          // Create button
          SizedBox(
            width: double.infinity,
            // Dimension: the full-width primary CTA's fixed height.
            height: 52,
            // `FuzzzyButton`'s disabled visual is Opacity(0.42) over the SAME
            // fill (buttons/fuzzzy_button.dart:174), never a faded second
            // colour — the fork used `accentColor.withValues(alpha: 0.5)`.
            child: Opacity(
              opacity: _isCreating ? 0.42 : 1.0,
              child: ElevatedButton(
                onPressed: _isCreating ? null : _createCase,
                style: ElevatedButton.styleFrom(
                  backgroundColor: colors.actionPrimaryBg,
                  foregroundColor: colors.actionPrimaryFg,
                  disabledBackgroundColor: colors.actionPrimaryBg,
                  disabledForegroundColor: colors.actionPrimaryFg,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(radius.m),
                  ),
                  textStyle: type.control,
                ),
                child: _isCreating
                    ? SizedBox(
                        // Dimension: the in-button spinner's footprint.
                        width: 24,
                        height: 24,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: colors.actionPrimaryFg,
                        ),
                      )
                    : const Text('შექმნა და დაწყება →'),
              ),
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

/// `FuzzzyChipGroup` + `FuzzzyFilterChip`'s `dotColor` variant, app-side
/// (`harvest/mol.md` §1 routes this grid there at M11).
///
/// The kit's recipe verbatim (inputs/fuzzzy_filter_chip.dart:105-130): selected
/// is inverted-mono from the action pair — **never** a tint of the taxonomy
/// colour — the 1px border is CONSTANT and only recolours, and the domain
/// colour survives only as the 8px leading disc.
class _DomainPickerGrid extends StatelessWidget {
  const _DomainPickerGrid({
    required this.selectedDomain,
    required this.onDomainSelected,
  });

  final LegalDomain selectedDomain;
  final ValueChanged<LegalDomain> onDomainSelected;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final motion = context.fuzzzyMotion;
    final domainColors = context.legalDomainColors;

    return Wrap(
      spacing: space.s,
      runSpacing: space.s,
      children: LegalDomain.values.map((domain) {
        final isSelected = domain == selectedDomain;

        return FuzzzyHitTarget(
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTap: () => onDomainSelected(domain),
            child: AnimatedContainer(
              duration: motion.fast,
              curve: motion.fastCurve,
              padding: density.chip,
              decoration: BoxDecoration(
                // Parent is the sheet's `raised` rung, so the resting chip
                // takes the step down to `surface`.
                color: isSelected ? colors.actionPrimaryBg : colors.surface,
                borderRadius: BorderRadius.circular(radius.s),
                // 🔴 The fork grew this border 1→2px on selection, so picking
                // a domain reflowed the whole Wrap — potentially to a
                // different number of rows. Constant width, colour only
                // (fuzzzy_button.dart:84-87).
                border: Border.all(
                  color: isSelected ? colors.actionPrimaryBg : colors.line,
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    // §4.4's one status-dot diameter.
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: domainColors.of(domain),
                      borderRadius: BorderRadius.circular(radius.circle),
                    ),
                  ),
                  SizedBox(width: space.s),
                  Text(
                    domain.shortLabelKa,
                    style: type.control.copyWith(
                      color: isSelected ? colors.actionPrimaryFg : colors.inkMute,
                    ),
                  ),
                ],
              ),
            ),
          ),
        );
      }).toList(),
    );
  }
}
