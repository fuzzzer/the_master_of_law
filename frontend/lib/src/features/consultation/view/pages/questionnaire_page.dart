import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

class QuestionnairePage extends StatefulWidget {
  final String conversationId;
  final String domain;
  final String userDescription;

  const QuestionnairePage({
    super.key,
    required this.conversationId,
    required this.domain,
    required this.userDescription,
  });

  @override
  State<QuestionnairePage> createState() => _QuestionnairePageState();
}

class _QuestionnairePageState extends State<QuestionnairePage> {
  final _textController = TextEditingController();
  final _numberController = TextEditingController();
  String? _selectedChoice;
  bool? _booleanAnswer;
  DateTime? _selectedDate;

  @override
  void initState() {
    super.initState();
    context.read<QuestionnaireCubit>().generateQuestionnaire(
      conversationId: widget.conversationId,
      domain: widget.domain,
      userDescription: widget.userDescription,
    );
  }

  @override
  void dispose() {
    _textController.dispose();
    _numberController.dispose();
    super.dispose();
  }

  void _resetInputs() {
    _textController.clear();
    _numberController.clear();
    _selectedChoice = null;
    _booleanAnswer = null;
    _selectedDate = null;
  }

  void _prefillForCurrentQuestion(QuestionnaireState state) {
    final existingAnswer = state.currentAnswer;
    if (existingAnswer == null) {
      _resetInputs();
      return;
    }
    final question = state.currentQuestion!;
    switch (question.questionType) {
      case 'text':
        _textController.text = existingAnswer;
      case 'number':
        _numberController.text = existingAnswer;
      case 'boolean':
        _booleanAnswer = existingAnswer == 'true' || existingAnswer == 'დიახ';
      case 'choice':
        _selectedChoice = existingAnswer;
      case 'date':
        _selectedDate = DateTime.tryParse(existingAnswer);
      default:
        _textController.text = existingAnswer;
    }
  }

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Scaffold(
      appBar: AppBar(
        title: Text('კითხვარი', style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor)),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: BlocConsumer<QuestionnaireCubit, QuestionnaireState>(
        listenWhen: (prev, curr) =>
            prev.currentIndex != curr.currentIndex || prev.isComplete != curr.isComplete,
        listener: (context, state) {
          if (state.isComplete) {
            _showReviewPage(context, state);
            return;
          }
          _prefillForCurrentQuestion(state);
        },
        builder: (context, state) {
          if (state.status == StateStatus.loading) {
            return _buildLoading(context);
          }
          if (state.status == StateStatus.failed) {
            return _buildError(context, state);
          }
          if (state.questions.isEmpty) {
            return _buildLoading(context);
          }
          return Column(
            children: [
              _buildProgressBar(context, state),
              Expanded(
                child: AnimatedSwitcher(
                  duration: const Duration(milliseconds: 300),
                  transitionBuilder: (child, animation) => FadeTransition(
                    opacity: animation,
                    child: SlideTransition(
                      position: Tween<Offset>(
                        begin: const Offset(0.05, 0),
                        end: Offset.zero,
                      ).animate(animation),
                      child: child,
                    ),
                  ),
                  child: KeyedSubtree(
                    key: ValueKey(state.currentIndex),
                    child: _buildQuestionCard(context, state),
                  ),
                ),
              ),
              _buildBottomBar(context, state),
            ],
          );
        },
      ),
    );
  }

  Widget _buildLoading(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(color: uiColors.accentColor),
          const SizedBox(height: 16),
          Text(
            'კითხვები მზადდება...',
            style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
          ),
        ],
      ),
    );
  }

  Widget _buildError(BuildContext context, QuestionnaireState state) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 48, color: uiColors.accentColor.withValues(alpha: 0.7)),
            const SizedBox(height: 16),
            Text(
              'კითხვარის გენერაცია ვერ მოხერხდა',
              style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => context.read<QuestionnaireCubit>().generateQuestionnaire(
                conversationId: widget.conversationId,
                domain: widget.domain,
                userDescription: widget.userDescription,
              ),
              child: const Text('ხელახლა ცდა'),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProgressBar(BuildContext context, QuestionnaireState state) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final progress = state.questions.isEmpty ? 0.0 : (state.currentIndex + 1) / state.questions.length;

    return Container(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 12),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${state.currentIndex + 1}/${state.questions.length}',
                style: uiTextStyles.bodyBold14.copyWith(color: uiColors.accentColor),
              ),
              Text(
                '${state.answeredCount} პასუხგაცემული',
                style: uiTextStyles.caption11.copyWith(color: uiColors.secondaryTextColor),
              ),
            ],
          ),
          const SizedBox(height: 6),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: progress,
              backgroundColor: uiColors.secondaryTextColor.withValues(alpha: 0.1),
              valueColor: AlwaysStoppedAnimation(uiColors.accentColor),
              minHeight: 4,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuestionCard(BuildContext context, QuestionnaireState state) {
    final question = state.currentQuestion;
    if (question == null) return const SizedBox.shrink();

    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 8),
          if (question.required)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              margin: const EdgeInsets.only(bottom: 8),
              decoration: BoxDecoration(
                color: uiColors.accentColor.withValues(alpha: 0.1),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                'სავალდებულო',
                style: uiTextStyles.caption11.copyWith(
                  color: uiColors.accentColor,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          Text(
            question.questionText,
            style: uiTextStyles.headlineBold20.copyWith(
              color: uiColors.primaryTextColor,
              height: 1.4,
            ),
          ),
          if (question.purpose != null && question.purpose!.isNotEmpty) ...[
            const SizedBox(height: 8),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.info_outline, size: 14, color: uiColors.secondaryTextColor),
                const SizedBox(width: 6),
                Expanded(
                  child: Text(
                    question.purpose!,
                    style: uiTextStyles.caption11.copyWith(
                      color: uiColors.secondaryTextColor,
                      height: 1.4,
                    ),
                  ),
                ),
              ],
            ),
          ],
          const SizedBox(height: 24),
          _buildInputWidget(context, question),
        ],
      ),
    );
  }

  Widget _buildInputWidget(BuildContext context, QuestionnaireQuestionModel question) {
    return switch (question.questionType) {
      'text' => _buildTextInput(context),
      'boolean' => _buildBooleanInput(context),
      'choice' => _buildChoiceInput(context, question),
      'date' => _buildDateInput(context),
      'number' => _buildNumberInput(context),
      _ => _buildTextInput(context),
    };
  }

  Widget _buildTextInput(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    return TextField(
      controller: _textController,
      maxLines: 5,
      minLines: 3,
      style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
      decoration: InputDecoration(
        hintText: 'შეიყვანეთ პასუხი...',
        hintStyle: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
        filled: true,
        fillColor: uiColors.backgroundSecondaryColor,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: uiColors.secondaryTextColor.withValues(alpha: 0.2)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: uiColors.secondaryTextColor.withValues(alpha: 0.2)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: uiColors.accentColor),
        ),
      ),
    );
  }

  Widget _buildBooleanInput(BuildContext context) {
    return Row(
      children: [
        Expanded(child: _buildBooleanOption(context, 'დიახ', true)),
        const SizedBox(width: 12),
        Expanded(child: _buildBooleanOption(context, 'არა', false)),
      ],
    );
  }

  Widget _buildBooleanOption(BuildContext context, String label, bool value) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final isSelected = _booleanAnswer == value;
    return GestureDetector(
      onTap: () => setState(() => _booleanAnswer = value),
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: isSelected ? uiColors.accentColor.withValues(alpha: 0.15) : uiColors.backgroundSecondaryColor,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isSelected ? uiColors.accentColor : uiColors.secondaryTextColor.withValues(alpha: 0.2),
            width: isSelected ? 2 : 1,
          ),
        ),
        child: Center(
          child: Text(
            label,
            style: uiTextStyles.bodyBold16.copyWith(
              color: isSelected ? uiColors.accentColor : uiColors.primaryTextColor,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildChoiceInput(BuildContext context, QuestionnaireQuestionModel question) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final options = question.options ?? [];

    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: options.map((option) {
        final isSelected = _selectedChoice == option;
        return GestureDetector(
          onTap: () => setState(() => _selectedChoice = option),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              color: isSelected ? uiColors.accentColor.withValues(alpha: 0.15) : uiColors.backgroundSecondaryColor,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: isSelected ? uiColors.accentColor : uiColors.secondaryTextColor.withValues(alpha: 0.2),
              ),
            ),
            child: Text(
              option,
              style: uiTextStyles.body14.copyWith(
                color: isSelected ? uiColors.accentColor : uiColors.primaryTextColor,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildDateInput(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    return GestureDetector(
      onTap: () async {
        final picked = await showDatePicker(
          context: context,
          initialDate: _selectedDate ?? DateTime.now(),
          firstDate: DateTime(1950),
          lastDate: DateTime.now(),
          locale: const Locale('ka'),
        );
        if (picked != null) {
          setState(() => _selectedDate = picked);
        }
      },
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        decoration: BoxDecoration(
          color: uiColors.backgroundSecondaryColor,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: _selectedDate != null
                ? uiColors.accentColor
                : uiColors.secondaryTextColor.withValues(alpha: 0.2),
          ),
        ),
        child: Row(
          children: [
            Icon(Icons.calendar_today, size: 18, color: uiColors.secondaryTextColor),
            const SizedBox(width: 10),
            Text(
              _selectedDate != null
                  ? '${_selectedDate!.day.toString().padLeft(2, '0')}/${_selectedDate!.month.toString().padLeft(2, '0')}/${_selectedDate!.year}'
                  : 'აირჩიეთ თარიღი',
              style: uiTextStyles.body14.copyWith(
                color: _selectedDate != null ? uiColors.primaryTextColor : uiColors.secondaryTextColor,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNumberInput(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    return TextField(
      controller: _numberController,
      keyboardType: TextInputType.number,
      style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
      decoration: InputDecoration(
        hintText: 'შეიყვანეთ რიცხვი',
        hintStyle: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
        filled: true,
        fillColor: uiColors.backgroundSecondaryColor,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: uiColors.secondaryTextColor.withValues(alpha: 0.2)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: uiColors.secondaryTextColor.withValues(alpha: 0.2)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: uiColors.accentColor),
        ),
      ),
    );
  }

  Widget _buildBottomBar(BuildContext context, QuestionnaireState state) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;
    final question = state.currentQuestion;

    return Container(
      padding: EdgeInsets.fromLTRB(20, 12, 20, MediaQuery.of(context).padding.bottom + 12),
      decoration: BoxDecoration(
        color: uiColors.backgroundSecondaryColor,
        border: Border(top: BorderSide(color: uiColors.secondaryTextColor.withValues(alpha: 0.1))),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Row(
            children: [
              if (!state.isFirstQuestion)
                TextButton.icon(
                  onPressed: () {
                    context.read<QuestionnaireCubit>().goToPreviousQuestion();
                    _prefillForCurrentQuestion(state);
                  },
                  icon: const Icon(Icons.arrow_back, size: 18),
                  label: const Text('წინა'),
                )
              else
                const SizedBox(width: 80),
              const Spacer(),
              if (question != null && !question.required)
                TextButton(
                  onPressed: state.isSubmitting ? null : () => _submitCurrentAnswer(context, state, skip: true),
                  child: Text(
                    'გამოტოვება',
                    style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                  ),
                ),
              const SizedBox(width: 8),
              ElevatedButton(
                onPressed: state.isSubmitting ? null : () => _submitCurrentAnswer(context, state),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                ),
                child: state.isSubmitting
                    ? SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2, color: uiColors.accentColor))
                    : Text(state.isLastQuestion ? 'დასრულება' : 'შემდეგი'),
              ),
            ],
          ),
          if (_hasRemainingOptionalQuestions(state)) ...[
            const SizedBox(height: 8),
            TextButton(
              onPressed: state.isSubmitting ? null : () => context.read<QuestionnaireCubit>().skipRemaining(),
              child: Text(
                'არასავალდებულოების გამოტოვება',
                style: uiTextStyles.caption11.copyWith(
                  color: uiColors.secondaryTextColor,
                  decoration: TextDecoration.underline,
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }

  bool _hasRemainingOptionalQuestions(QuestionnaireState state) {
    return state.questions
        .where((q) => !q.required && !state.answers.containsKey(q.questionId))
        .isNotEmpty;
  }

  void _showReviewPage(BuildContext context, QuestionnaireState state) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => QuestionnaireReviewPage(
          questions: state.questions,
          answers: state.answers,
          onConfirm: () {
            Navigator.of(context).pop();
            Navigator.of(context).pop(true);
          },
          onEdit: () {
            Navigator.of(context).pop();
            context.read<QuestionnaireCubit>().goToPreviousQuestion();
          },
        ),
      ),
    );
  }

  void _submitCurrentAnswer(BuildContext context, QuestionnaireState state, {bool skip = false}) {
    final question = state.currentQuestion;
    if (question == null) return;

    if (skip) {
      context.read<QuestionnaireCubit>().submitAnswer('');
      return;
    }

    final answer = _getAnswerValue(question);
    final validationError = _validateAnswer(answer, question);
    if (validationError != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(validationError), duration: const Duration(seconds: 2)),
      );
      return;
    }

    context.read<QuestionnaireCubit>().submitAnswer(answer!);
  }

  String? _validateAnswer(String? answer, QuestionnaireQuestionModel question) {
    if (answer == null || answer.isEmpty) {
      if (question.required) return 'ეს ველი სავალდებულოა';
      return null;
    }
    if (question.questionType == 'text' && question.required && answer.length < 5) {
      return 'მინიმუმ 5 სიმბოლო აუცილებელია';
    }
    return null;
  }

  String? _getAnswerValue(QuestionnaireQuestionModel question) {
    return switch (question.questionType) {
      'text' => _textController.text.trim(),
      'number' => _numberController.text.trim(),
      'boolean' => _booleanAnswer != null ? (_booleanAnswer! ? 'დიახ' : 'არა') : null,
      'choice' => _selectedChoice,
      'date' => _selectedDate?.toIso8601String(),
      _ => _textController.text.trim(),
    };
  }
}
