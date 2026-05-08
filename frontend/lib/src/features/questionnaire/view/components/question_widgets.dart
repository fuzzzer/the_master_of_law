import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:themasteroflaw/src/src.dart';

/// Base interface for all question input widgets.
abstract class QuestionInputWidget extends StatefulWidget {
  final QuestionnaireQuestion question;
  final String? initialValue;
  final ValueChanged<String> onChanged;
  final VoidCallback? onSubmit;

  const QuestionInputWidget({
    super.key,
    required this.question,
    this.initialValue,
    required this.onChanged,
    this.onSubmit,
  });
}

/// Multi-line text input for free-form answers.
class TextQuestionWidget extends QuestionInputWidget {
  const TextQuestionWidget({
    super.key,
    required super.question,
    super.initialValue,
    required super.onChanged,
    super.onSubmit,
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

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: _controller,
      maxLines: 5,
      minLines: 3,
      textInputAction: TextInputAction.done,
      keyboardType: TextInputType.multiline,
      onChanged: widget.onChanged,
      onSubmitted: widget.onSubmit != null ? (_) => widget.onSubmit!() : null,
      decoration: InputDecoration(
        hintText: 'ჩაწერეთ პასუხი...',
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        contentPadding: const EdgeInsets.all(16),
      ),
    );
  }
}

/// Yes/No toggle for boolean questions.
class BooleanQuestionWidget extends QuestionInputWidget {
  const BooleanQuestionWidget({
    super.key,
    required super.question,
    super.initialValue,
    required super.onChanged,
    super.onSubmit,
  });

  @override
  State<BooleanQuestionWidget> createState() => _BooleanQuestionWidgetState();
}

class _BooleanQuestionWidgetState extends State<BooleanQuestionWidget> {
  bool? _value;

  @override
  void initState() {
    super.initState();
    if (widget.initialValue != null) {
      final v = widget.initialValue!.toLowerCase().trim();
      _value = v == 'true' || v == 'კი' || v == 'დიახ' || v == 'yes';
    }
  }

  void _select(bool value) {
    setState(() => _value = value);
    widget.onChanged(value ? 'კი' : 'არა');
    widget.onSubmit?.call();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Row(
      children: [
        Expanded(
          child: _ToggleCard(
            label: 'კი',
            selected: _value == true,
            onTap: () => _select(true),
            activeColor: theme.colorScheme.primary,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: _ToggleCard(
            label: 'არა',
            selected: _value == false,
            onTap: () => _select(false),
            activeColor: theme.colorScheme.error,
          ),
        ),
      ],
    );
  }
}

class _ToggleCard extends StatelessWidget {
  final String label;
  final bool selected;
  final VoidCallback onTap;
  final Color activeColor;

  const _ToggleCard({
    required this.label,
    required this.selected,
    required this.onTap,
    required this.activeColor,
  });

  @override
  Widget build(BuildContext context) {
    return Material(
      color: selected ? activeColor.withOpacity(0.12) : Colors.grey.shade50,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(vertical: 20),
          alignment: Alignment.center,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: selected ? activeColor : Colors.grey.shade300,
              width: selected ? 2 : 1,
            ),
          ),
          child: Text(
            label,
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w600,
              color: selected ? activeColor : Colors.black87,
            ),
          ),
        ),
      ),
    );
  }
}

/// Radio buttons / choice chips for single-select questions.
class ChoiceQuestionWidget extends QuestionInputWidget {
  const ChoiceQuestionWidget({
    super.key,
    required super.question,
    super.initialValue,
    required super.onChanged,
    super.onSubmit,
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

  void _select(String value) {
    setState(() => _selected = value);
    widget.onChanged(value);
    widget.onSubmit?.call();
  }

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: widget.question.options.map((option) {
        final isSelected = _selected == option;
        return ChoiceChip(
          label: Text(option),
          selected: isSelected,
          onSelected: (_) => _select(option),
          selectedColor: Theme.of(context).colorScheme.primaryContainer,
          labelStyle: TextStyle(
            color: isSelected
                ? Theme.of(context).colorScheme.onPrimaryContainer
                : Colors.black87,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
          ),
        );
      }).toList(),
    );
  }
}

/// Date picker for date questions.
class DateQuestionWidget extends QuestionInputWidget {
  const DateQuestionWidget({
    super.key,
    required super.question,
    super.initialValue,
    required super.onChanged,
    super.onSubmit,
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
      lastDate: now,
      locale: const Locale('ka', 'GE'),
    );
    if (picked != null) {
      setState(() => _selectedDate = picked);
      final formatted = DateFormat('yyyy-MM-dd').format(picked);
      widget.onChanged(formatted);
    }
  }

  @override
  Widget build(BuildContext context) {
    final displayText = _selectedDate != null
        ? DateFormat('dd MMMM, yyyy', 'ka').format(_selectedDate!)
        : 'აირჩიეთ თარიღი';

    return Material(
      color: Colors.grey.shade50,
      borderRadius: BorderRadius.circular(12),
      child: InkWell(
        onTap: _pickDate,
        borderRadius: BorderRadius.circular(12),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 18),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey.shade300),
          ),
          child: Row(
            children: [
              Icon(
                Icons.calendar_today_outlined,
                color: Theme.of(context).colorScheme.primary,
              ),
              const SizedBox(width: 12),
              Text(
                displayText,
                style: TextStyle(
                  fontSize: 16,
                  color: _selectedDate != null ? Colors.black87 : Colors.grey.shade600,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

/// Number input for numeric questions (amounts, durations, etc.).
class NumberQuestionWidget extends QuestionInputWidget {
  const NumberQuestionWidget({
    super.key,
    required super.question,
    super.initialValue,
    required super.onChanged,
    super.onSubmit,
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

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: _controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'^[0-9]*\.?[0-9]*'))],
      textInputAction: TextInputAction.done,
      onChanged: widget.onChanged,
      onSubmitted: widget.onSubmit != null ? (_) => widget.onSubmit!() : null,
      decoration: InputDecoration(
        hintText: 'შეიყვანეთ რიცხვი...',
        suffixText: 'GEL',
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        contentPadding: const EdgeInsets.all(16),
      ),
    );
  }
}

/// Factory to build the correct widget for a question type.
Widget buildQuestionInput({
  required QuestionnaireQuestion question,
  String? initialValue,
  required ValueChanged<String> onChanged,
  VoidCallback? onSubmit,
}) {
  switch (question.questionType) {
    case 'boolean':
      return BooleanQuestionWidget(
        question: question,
        initialValue: initialValue,
        onChanged: onChanged,
        onSubmit: onSubmit,
      );
    case 'choice':
      return ChoiceQuestionWidget(
        question: question,
        initialValue: initialValue,
        onChanged: onChanged,
        onSubmit: onSubmit,
      );
    case 'date':
      return DateQuestionWidget(
        question: question,
        initialValue: initialValue,
        onChanged: onChanged,
        onSubmit: onSubmit,
      );
    case 'number':
      return NumberQuestionWidget(
        question: question,
        initialValue: initialValue,
        onChanged: onChanged,
        onSubmit: onSubmit,
      );
    case 'text':
    default:
      return TextQuestionWidget(
        question: question,
        initialValue: initialValue,
        onChanged: onChanged,
        onSubmit: onSubmit,
      );
  }
}
