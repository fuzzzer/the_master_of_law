import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:themasteroflaw/src/core/extensions/build_context_extenstion.dart';

/// Base interface for all question widgets.
/// Each widget captures user input and calls [onAnswer] when the user
/// confirms their response.
abstract class QuestionWidget extends StatelessWidget {
  final String questionText;
  final bool required;
  final void Function(String answer) onAnswer;
  final String? initialValue;

  const QuestionWidget({
    super.key,
    required this.questionText,
    required this.required,
    required this.onAnswer,
    this.initialValue,
  });
}

// ── Text Question ───────────────────────────────────────────────

class TextQuestionWidget extends StatefulWidget implements QuestionWidget {
  @override
  final String questionText;
  @override
  final bool required;
  @override
  final void Function(String answer) onAnswer;
  @override
  final String? initialValue;

  const TextQuestionWidget({
    super.key,
    required this.questionText,
    required this.required,
    required this.onAnswer,
    this.initialValue,
  });

  @override
  State<TextQuestionWidget> createState() => _TextQuestionWidgetState();
}

class _TextQuestionWidgetState extends State<TextQuestionWidget> {
  late final TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialValue ?? '');
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    final text = _controller.text.trim();
    if (text.isEmpty && widget.required) return;
    widget.onAnswer(text);
  }

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.questionText,
          style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
        ),
        if (!widget.required)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              'არასავალდებულო',
              style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
            ),
          ),
        const SizedBox(height: 16),
        TextField(
          controller: _controller,
          style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
          keyboardType: TextInputType.multiline,
          textInputAction: TextInputAction.done,
          textCapitalization: TextCapitalization.sentences,
          maxLines: 5,
          minLines: 3,
          onSubmitted: (_) => _submit(),
          decoration: InputDecoration(
            hintText: 'დაწერეთ პასუხი...',
            hintStyle: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
            filled: true,
            fillColor: uiColors.surfaceColor,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide.none,
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          ),
        ),
        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          height: 50,
          child: ElevatedButton(
            onPressed: _submit,
            style: ElevatedButton.styleFrom(
              backgroundColor: uiColors.accentColor,
              foregroundColor: uiColors.backgroundPrimaryColor,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: Text(
              'შემდეგი',
              style: uiTextStyles.bodyBold14,
            ),
          ),
        ),
      ],
    );
  }
}

// ── Boolean Question ────────────────────────────────────────────

class BooleanQuestionWidget extends StatefulWidget implements QuestionWidget {
  @override
  final String questionText;
  @override
  final bool required;
  @override
  final void Function(String answer) onAnswer;
  @override
  final String? initialValue;

  const BooleanQuestionWidget({
    super.key,
    required this.questionText,
    required this.required,
    required this.onAnswer,
    this.initialValue,
  });

  @override
  State<BooleanQuestionWidget> createState() => _BooleanQuestionWidgetState();
}

class _BooleanQuestionWidgetState extends State<BooleanQuestionWidget> {
  bool? _selected;

  @override
  void initState() {
    super.initState();
    if (widget.initialValue != null) {
      _selected = widget.initialValue!.toLowerCase() == 'კი' ||
          widget.initialValue!.toLowerCase() == 'true' ||
          widget.initialValue!.toLowerCase() == 'yes';
    }
  }

  void _submit(bool value) {
    widget.onAnswer(value ? 'კი' : 'არა');
  }

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.questionText,
          style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
        ),
        if (!widget.required)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              'არასავალდებულო',
              style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
            ),
          ),
        const SizedBox(height: 24),
        Row(
          children: [
            Expanded(
              child: _BooleanOption(
                label: 'კი',
                isSelected: _selected == true,
                onTap: () => _submit(true),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _BooleanOption(
                label: 'არა',
                isSelected: _selected == false,
                onTap: () => _submit(false),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _BooleanOption extends StatelessWidget {
  final String label;
  final bool isSelected;
  final VoidCallback onTap;

  const _BooleanOption({
    required this.label,
    required this.isSelected,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return GestureDetector(
      onTap: onTap,
      child: Container(
        height: 56,
        decoration: BoxDecoration(
          color: isSelected
              ? uiColors.accentColor.withValues(alpha: 0.15)
              : uiColors.surfaceColor,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isSelected
                ? uiColors.accentColor
                : uiColors.secondaryTextColor.withValues(alpha: 0.2),
            width: isSelected ? 2 : 1,
          ),
        ),
        alignment: Alignment.center,
        child: Text(
          label,
          style: uiTextStyles.bodyBold16.copyWith(
            color: isSelected ? uiColors.accentColor : uiColors.primaryTextColor,
          ),
        ),
      ),
    );
  }
}

// ── Choice Question ─────────────────────────────────────────────

class ChoiceQuestionWidget extends StatefulWidget implements QuestionWidget {
  @override
  final String questionText;
  @override
  final bool required;
  @override
  final void Function(String answer) onAnswer;
  @override
  final String? initialValue;
  final List<String> options;

  const ChoiceQuestionWidget({
    super.key,
    required this.questionText,
    required this.required,
    required this.onAnswer,
    this.initialValue,
    required this.options,
  });

  @override
  State<ChoiceQuestionWidget> createState() => _ChoiceQuestionWidgetState();
}

class _ChoiceQuestionWidgetState extends State<ChoiceQuestionWidget> {
  String? _selected;

  @override
  void initState() {
    super.initState();
    _selected = widget.initialValue;
  }

  void _submit() {
    if (_selected == null && widget.required) return;
    widget.onAnswer(_selected ?? '');
  }

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.questionText,
          style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
        ),
        if (!widget.required)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              'არასავალდებულო',
              style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
            ),
          ),
        const SizedBox(height: 16),
        ...widget.options.map((option) {
          final isSelected = _selected == option;
          return Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: GestureDetector(
              onTap: () {
                setState(() => _selected = option);
              },
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                decoration: BoxDecoration(
                  color: isSelected
                      ? uiColors.accentColor.withValues(alpha: 0.12)
                      : uiColors.surfaceColor,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: isSelected
                        ? uiColors.accentColor
                        : uiColors.secondaryTextColor.withValues(alpha: 0.15),
                    width: isSelected ? 2 : 1,
                  ),
                ),
                child: Row(
                  children: [
                    Container(
                      width: 22,
                      height: 22,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: isSelected ? uiColors.accentColor : uiColors.secondaryTextColor,
                          width: 2,
                        ),
                      ),
                      child: isSelected
                          ? Center(
                              child: Container(
                                width: 10,
                                height: 10,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: uiColors.accentColor,
                                ),
                              ),
                            )
                          : null,
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        option,
                        style: uiTextStyles.body14.copyWith(
                          color: uiColors.primaryTextColor,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        }),
        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          height: 50,
          child: ElevatedButton(
            onPressed: (_selected != null || !widget.required) ? _submit : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: uiColors.accentColor,
              foregroundColor: uiColors.backgroundPrimaryColor,
              disabledBackgroundColor: uiColors.secondaryTextColor.withValues(alpha: 0.2),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: Text(
              'შემდეგი',
              style: uiTextStyles.bodyBold14,
            ),
          ),
        ),
      ],
    );
  }
}

// ── Date Question ───────────────────────────────────────────────

class DateQuestionWidget extends StatefulWidget implements QuestionWidget {
  @override
  final String questionText;
  @override
  final bool required;
  @override
  final void Function(String answer) onAnswer;
  @override
  final String? initialValue;

  const DateQuestionWidget({
    super.key,
    required this.questionText,
    required this.required,
    required this.onAnswer,
    this.initialValue,
  });

  @override
  State<DateQuestionWidget> createState() => _DateQuestionWidgetState();
}

class _DateQuestionWidgetState extends State<DateQuestionWidget> {
  DateTime? _selectedDate;

  @override
  void initState() {
    super.initState();
    if (widget.initialValue != null && widget.initialValue!.isNotEmpty) {
      _selectedDate = DateTime.tryParse(widget.initialValue!);
    }
  }

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate ?? now,
      firstDate: DateTime(1900),
      lastDate: DateTime(now.year + 5),
      builder: (context, child) {
        final uiColors = context.uiColors;
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: ColorScheme.dark(
              primary: uiColors.accentColor,
              onPrimary: uiColors.backgroundPrimaryColor,
              surface: uiColors.backgroundSecondaryColor,
              onSurface: uiColors.primaryTextColor,
            ),
            dialogBackgroundColor: uiColors.backgroundPrimaryColor,
          ),
          child: child!,
        );
      },
    );
    if (picked != null) {
      setState(() => _selectedDate = picked);
    }
  }

  void _submit() {
    if (_selectedDate == null && widget.required) return;
    final formatted = _selectedDate != null
        ? '${_selectedDate!.year.toString().padLeft(4, '0')}-${_selectedDate!.month.toString().padLeft(2, '0')}-${_selectedDate!.day.toString().padLeft(2, '0')}'
        : '';
    widget.onAnswer(formatted);
  }

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.questionText,
          style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
        ),
        if (!widget.required)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              'არასავალდებულო',
              style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
            ),
          ),
        const SizedBox(height: 16),
        GestureDetector(
          onTap: _pickDate,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            decoration: BoxDecoration(
              color: uiColors.surfaceColor,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              children: [
                Icon(Icons.calendar_today, color: uiColors.secondaryTextColor, size: 20),
                const SizedBox(width: 12),
                Text(
                  _selectedDate != null
                      ? '${_selectedDate!.day.toString().padLeft(2, '0')}/${_selectedDate!.month.toString().padLeft(2, '0')}/${_selectedDate!.year}'
                      : 'აირჩიეთ თარიღი',
                  style: uiTextStyles.body14.copyWith(
                    color: _selectedDate != null
                        ? uiColors.primaryTextColor
                        : uiColors.secondaryTextColor,
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          height: 50,
          child: ElevatedButton(
            onPressed: (_selectedDate != null || !widget.required) ? _submit : null,
            style: ElevatedButton.styleFrom(
              backgroundColor: uiColors.accentColor,
              foregroundColor: uiColors.backgroundPrimaryColor,
              disabledBackgroundColor: uiColors.secondaryTextColor.withValues(alpha: 0.2),
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: Text(
              'შემდეგი',
              style: uiTextStyles.bodyBold14,
            ),
          ),
        ),
      ],
    );
  }
}

// ── Number Question ─────────────────────────────────────────────

class NumberQuestionWidget extends StatefulWidget implements QuestionWidget {
  @override
  final String questionText;
  @override
  final bool required;
  @override
  final void Function(String answer) onAnswer;
  @override
  final String? initialValue;

  const NumberQuestionWidget({
    super.key,
    required this.questionText,
    required this.required,
    required this.onAnswer,
    this.initialValue,
  });

  @override
  State<NumberQuestionWidget> createState() => _NumberQuestionWidgetState();
}

class _NumberQuestionWidgetState extends State<NumberQuestionWidget> {
  late final TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController(text: widget.initialValue ?? '');
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _submit() {
    final text = _controller.text.trim();
    if (text.isEmpty && widget.required) return;
    widget.onAnswer(text);
  }

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.questionText,
          style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
        ),
        if (!widget.required)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              'არასავალდებულო',
              style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
            ),
          ),
        const SizedBox(height: 16),
        TextField(
          controller: _controller,
          style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          textInputAction: TextInputAction.done,
          inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[0-9.,]'))],
          onSubmitted: (_) => _submit(),
          decoration: InputDecoration(
            hintText: 'შეიყვანეთ რიცხვი...',
            hintStyle: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
            filled: true,
            fillColor: uiColors.surfaceColor,
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(12),
              borderSide: BorderSide.none,
            ),
            contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          ),
        ),
        const SizedBox(height: 16),
        SizedBox(
          width: double.infinity,
          height: 50,
          child: ElevatedButton(
            onPressed: _submit,
            style: ElevatedButton.styleFrom(
              backgroundColor: uiColors.accentColor,
              foregroundColor: uiColors.backgroundPrimaryColor,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: Text(
              'შემდეგი',
              style: uiTextStyles.bodyBold14,
            ),
          ),
        ),
      ],
    );
  }
}
