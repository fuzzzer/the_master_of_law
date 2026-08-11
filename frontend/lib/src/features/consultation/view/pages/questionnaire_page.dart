import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
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
    final motion = context.fuzzzyMotion;

    return Scaffold(
      appBar: AppBar(
        // Title style comes from appBarTheme (titleM + ink), built from roles.
        title: const Text('კითხვარი'),
        leading: IconButton(
          icon: const Icon(Icons.close),
          onPressed: () => Navigator.of(context).pop(),
        ),
      ),
      body: BlocConsumer<QuestionnaireCubit, QuestionnaireState>(
        listenWhen: (prev, curr) =>
            prev.currentIndex != curr.currentIndex ||
            prev.isComplete != curr.isComplete,
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
                  // Genuine animation → a motion role (220ms + its curve).
                  duration: motion.standard,
                  switchInCurve: motion.standardCurve,
                  switchOutCurve: motion.standardCurve,
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
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(color: colors.ink),
          SizedBox(height: space.l),
          Text(
            'კითხვები მზადდება...',
            style: type.body.copyWith(color: colors.inkMute),
          ),
        ],
      ),
    );
  }

  Widget _buildError(BuildContext context, QuestionnaireState state) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final density = context.fuzzzyDensity;
    return Center(
      child: Padding(
        padding: density.screen,
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.error_outline, size: 48, color: colors.inkFaint),
            SizedBox(height: space.l),
            Text(
              'კითხვარის გენერაცია ვერ მოხერხდა',
              style: type.titleS.copyWith(color: colors.ink),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: space.xl),
            ElevatedButton(
              onPressed: () =>
                  context.read<QuestionnaireCubit>().generateQuestionnaire(
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
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final progress = state.questions.isEmpty
        ? 0.0
        : (state.currentIndex + 1) / state.questions.length;

    return Container(
      padding: EdgeInsets.fromLTRB(
        density.screen.left,
        space.s,
        density.screen.right,
        space.m,
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                '${state.currentIndex + 1}/${state.questions.length}',
                style: type.titleS.copyWith(color: colors.ink),
              ),
              Text(
                '${state.answeredCount} პასუხგაცემული',
                style: type.bodyS.copyWith(color: colors.inkMute),
              ),
            ],
          ),
          SizedBox(height: space.xs),
          ClipRRect(
            borderRadius: BorderRadius.circular(radius.l),
            child: LinearProgressIndicator(
              value: progress,
              // The empty rung of a progress bar IS `track` (MAPPING §2.3).
              backgroundColor: colors.track,
              valueColor: AlwaysStoppedAnimation(colors.ink),
              // Dimension: the bar's 4px rail.
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

    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return SingleChildScrollView(
      padding: density.screen.copyWith(top: 0, bottom: 0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(height: space.s),
          if (question.required)
            Container(
              padding: density.chip,
              margin: EdgeInsets.only(bottom: space.s),
              decoration: BoxDecoration(
                color: colors.surface,
                border: Border.all(color: colors.line),
                borderRadius: BorderRadius.circular(radius.s),
              ),
              child: Text(
                'სავალდებულო',
                // `control` IS the w600 role — no fontWeight override.
                style: type.control.copyWith(color: colors.ink),
              ),
            ),
          Text(
            question.questionText,
            // No `height:` override — the pack owns the type scale.
            style: type.titleM.copyWith(color: colors.ink),
          ),
          if (question.purpose != null && question.purpose!.isNotEmpty) ...[
            SizedBox(height: space.s),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(Icons.info_outline, size: 14, color: colors.inkMute),
                SizedBox(width: space.s),
                Expanded(
                  child: Text(
                    question.purpose!,
                    style: type.bodyS.copyWith(color: colors.inkMute),
                  ),
                ),
              ],
            ),
          ],
          SizedBox(height: space.xl),
          _buildInputWidget(context, question),
        ],
      ),
    );
  }

  Widget _buildInputWidget(
    BuildContext context,
    QuestionnaireQuestionModel question,
  ) {
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
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    return TextField(
      controller: _textController,
      maxLines: 5,
      minLines: 3,
      style: type.body.copyWith(color: colors.fieldText),
      // fill / idleBorder / focusBorder / errorBorder / disabledBorder and
      // contentPadding all come from inputDecorationTheme, built from the ten
      // kit form colour roles. The fork restated three of the five states.
      decoration: const InputDecoration(hintText: 'შეიყვანეთ პასუხი...'),
    );
  }

  Widget _buildBooleanInput(BuildContext context) {
    return Row(
      children: [
        Expanded(child: _buildBooleanOption(context, 'დიახ', true)),
        SizedBox(width: context.fuzzzySpace.m),
        Expanded(child: _buildBooleanOption(context, 'არა', false)),
      ],
    );
  }

  Widget _buildBooleanOption(BuildContext context, String label, bool value) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final isSelected = _booleanAnswer == value;
    // Inverted-mono selection, and a CONSTANT 1px border: the fork's
    // `width: isSelected ? 2 : 1` reflowed the row on every tap. States
    // recolour, never resize (buttons/fuzzzy_button.dart:84-87).
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTap: () => setState(() => _booleanAnswer = value),
      child: Container(
        padding: density.snug,
        decoration: BoxDecoration(
          color: isSelected ? colors.actionPrimaryBg : colors.surface,
          borderRadius: BorderRadius.circular(radius.m),
          border: Border.all(
            color: isSelected ? colors.actionPrimaryBg : colors.line,
          ),
        ),
        child: Center(
          child: Text(
            label,
            style: type.titleS.copyWith(
              color: isSelected ? colors.actionPrimaryFg : colors.ink,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildChoiceInput(
    BuildContext context,
    QuestionnaireQuestionModel question,
  ) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final options = question.options ?? [];

    // `FuzzzyFilterChip`'s recipe (inputs/fuzzzy_filter_chip.dart:92-112).
    // ONE label style for both states — the fork's w400/w600 swap re-measured
    // the chip on selection.
    return Wrap(
      spacing: space.s,
      runSpacing: space.s,
      children: options.map((option) {
        final isSelected = _selectedChoice == option;
        return GestureDetector(
          behavior: HitTestBehavior.opaque,
          onTap: () => setState(() => _selectedChoice = option),
          child: Container(
            padding: density.chip,
            decoration: BoxDecoration(
              color: isSelected ? colors.actionPrimaryBg : colors.surface,
              borderRadius: BorderRadius.circular(radius.s),
              border: Border.all(
                color: isSelected ? colors.actionPrimaryBg : colors.line,
              ),
            ),
            child: Text(
              option,
              style: type.control.copyWith(
                color: isSelected ? colors.actionPrimaryFg : colors.ink,
              ),
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildDateInput(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final form = context.fuzzzyFormStyles;
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
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
      // A tappable pseudo-field: it takes the FORM roles and FuzzzyFormStyles
      // geometry, so it is indistinguishable from the real TextFields above it.
      child: Container(
        width: double.infinity,
        padding: form.contentPadding,
        decoration: BoxDecoration(
          color: colors.fill,
          borderRadius: BorderRadius.circular(form.radius),
          border: Border.all(
            color: _selectedDate != null
                ? colors.lineStrong
                : colors.idleBorder,
            width: form.borderWidth,
          ),
        ),
        child: Row(
          children: [
            Icon(Icons.calendar_today, size: 18, color: colors.inkMute),
            SizedBox(width: space.s),
            Text(
              _selectedDate != null
                  ? '${_selectedDate!.day.toString().padLeft(2, '0')}/${_selectedDate!.month.toString().padLeft(2, '0')}/${_selectedDate!.year}'
                  : 'აირჩიეთ თარიღი',
              style: type.body.copyWith(
                color: _selectedDate != null ? colors.fieldText : colors.hint,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNumberInput(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    return TextField(
      controller: _numberController,
      keyboardType: TextInputType.number,
      style: type.body.copyWith(color: colors.fieldText),
      // fill / idleBorder / focusBorder / errorBorder / disabledBorder and
      // contentPadding all come from inputDecorationTheme, built from the ten
      // kit form colour roles. The fork restated three of the five states.
      decoration: const InputDecoration(hintText: 'შეიყვანეთ რიცხვი'),
    );
  }

  Widget _buildBottomBar(BuildContext context, QuestionnaireState state) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;
    final question = state.currentQuestion;

    return Container(
      padding: EdgeInsets.fromLTRB(
        density.screen.left,
        space.m,
        density.screen.right,
        MediaQuery.of(context).padding.bottom + space.m,
      ),
      decoration: BoxDecoration(
        color: colors.surface,
        border: Border(top: BorderSide(color: colors.line)),
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
                  style: TextButton.styleFrom(foregroundColor: colors.ink),
                  icon: const Icon(Icons.arrow_back, size: 18),
                  label: Text('წინა', style: type.control),
                )
              else
                // Dimension: reserves the back button's slot so the row does
                // not re-centre on the first question.
                const SizedBox(width: 80),
              const Spacer(),
              if (question != null && !question.required)
                TextButton(
                  onPressed: state.isSubmitting
                      ? null
                      : () => _submitCurrentAnswer(context, state, skip: true),
                  child: Text(
                    'გამოტოვება',
                    // `FuzzzyButton.ghost` idle foreground.
                    style: type.control.copyWith(color: colors.inkMute),
                  ),
                ),
              SizedBox(width: space.s),
              // `FuzzzyButton.primary`: actionPrimary pair, radius.m, `control`
              // label; disabled is Opacity(0.42), not a faded fill.
              Opacity(
                opacity: state.isSubmitting ? 0.42 : 1.0,
                child: ElevatedButton(
                  onPressed: state.isSubmitting
                      ? null
                      : () => _submitCurrentAnswer(context, state),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: colors.actionPrimaryBg,
                    foregroundColor: colors.actionPrimaryFg,
                    disabledBackgroundColor: colors.actionPrimaryBg,
                    disabledForegroundColor: colors.actionPrimaryFg,
                    padding: density.snug,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(radius.m),
                    ),
                  ),
                  child: state.isSubmitting
                      ? SizedBox(
                          // Dimension: the in-button spinner's footprint.
                          width: 18,
                          height: 18,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: colors.actionPrimaryFg,
                          ),
                        )
                      : Text(
                          state.isLastQuestion ? 'დასრულება' : 'შემდეგი',
                          style: type.control.copyWith(
                            color: colors.actionPrimaryFg,
                          ),
                        ),
                ),
              ),
            ],
          ),
          if (_hasRemainingOptionalQuestions(state)) ...[
            SizedBox(height: space.s),
            TextButton(
              onPressed: state.isSubmitting
                  ? null
                  : () => context.read<QuestionnaireCubit>().skipRemaining(),
              child: Text(
                'არასავალდებულოების გამოტოვება',
                style: type.bodyS.copyWith(
                  color: colors.inkMute,
                  decoration: TextDecoration.underline,
                  decorationColor: colors.inkMute,
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

  void _submitCurrentAnswer(
    BuildContext context,
    QuestionnaireState state, {
    bool skip = false,
  }) {
    final question = state.currentQuestion;
    if (question == null) return;

    if (skip) {
      context.read<QuestionnaireCubit>().submitAnswer('');
      return;
    }

    final answer = _getAnswerValue(question);
    final validationError = _validateAnswer(answer, question);
    if (validationError != null) {
      // A field-validation failure is red's sanctioned error duty, and the
      // toast is the only red on the screen while it is up.
      FuzzzyToast.show(
        context,
        message: validationError,
        kind: FuzzzyToastKind.error,
        qaId: 'questionnaire.validation',
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
    if (question.questionType == 'text' &&
        question.required &&
        answer.length < 5) {
      return 'მინიმუმ 5 სიმბოლო აუცილებელია';
    }
    return null;
  }

  String? _getAnswerValue(QuestionnaireQuestionModel question) {
    return switch (question.questionType) {
      'text' => _textController.text.trim(),
      'number' => _numberController.text.trim(),
      'boolean' =>
        _booleanAnswer != null ? (_booleanAnswer! ? 'დიახ' : 'არა') : null,
      'choice' => _selectedChoice,
      'date' => _selectedDate?.toIso8601String(),
      _ => _textController.text.trim(),
    };
  }
}
