import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

/// Full-screen questionnaire flow for dynamic legal intake.
///
/// This page handles:
/// - Question generation loading state
/// - One-at-a-time question display with type-specific inputs
/// - Progress indicator
/// - Skip button for optional questions
/// - Back navigation to edit previous answers
/// - Review screen with answer summary
class QuestionnairePage extends StatelessWidget {
  final String conversationId;
  final String legalDomain;
  final String? initialContext;

  const QuestionnairePage({
    super.key,
    required this.conversationId,
    required this.legalDomain,
    this.initialContext,
  });

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => QuestionnaireCubit(
        repository: QuestionnaireRepository(
          remoteDataSource: QuestionnaireRemoteDataSource(),
        ),
      )..startQuestionnaire(
          conversationId: conversationId,
          domain: legalDomain,
          context: initialContext ?? '',
        ),
      child: const _QuestionnairePageBody(),
    );
  }
}

class _QuestionnairePageBody extends StatefulWidget {
  const _QuestionnairePageBody();

  @override
  State<_QuestionnairePageBody> createState() => _QuestionnairePageBodyState();
}

class _QuestionnairePageBodyState extends State<_QuestionnairePageBody>
    with SingleTickerProviderStateMixin {
  late AnimationController _animController;
  late Animation<Offset> _slideAnimation;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _slideAnimation = Tween<Offset>(
      begin: const Offset(0.05, 0),
      end: Offset.zero,
    ).animate(CurvedAnimation(
      parent: _animController,
      curve: Curves.easeOutCubic,
    ));
    _animController.forward();
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('კითხვარი'),
        centerTitle: true,
        leading: BlocBuilder<QuestionnaireCubit, QuestionnaireState>(
          builder: (context, state) {
            if (state.canGoBack && state.status == QuestionnaireStatus.answering) {
              return IconButton(
                icon: const Icon(Icons.arrow_back),
                onPressed: () {
                  context.read<QuestionnaireCubit>().goBack();
                  _animController.forward(from: 0);
                },
              );
            }
            return const SizedBox.shrink();
          },
        ),
      ),
      body: SafeArea(
        child: BlocConsumer<QuestionnaireCubit, QuestionnaireState>(
          listener: (context, state) {
            if (state.status == QuestionnaireStatus.completed) {
              Navigator.of(context).pop(true);
            }
            if (state.status == QuestionnaireStatus.answering) {
              _animController.forward(from: 0);
            }
          },
          builder: (context, state) {
            return Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: AnimatedSwitcher(
                duration: const Duration(milliseconds: 250),
                child: _buildContent(context, state),
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildContent(BuildContext context, QuestionnaireState state) {
    switch (state.status) {
      case QuestionnaireStatus.initial:
      case QuestionnaireStatus.generating:
      case QuestionnaireStatus.loading:
        return const _LoadingView(key: ValueKey('loading'));

      case QuestionnaireStatus.answering:
      case QuestionnaireStatus.submitting:
        return _QuestionView(
          key: ValueKey('q_${state.currentQuestionIndex}'),
          state: state,
          animController: _animController,
          slideAnimation: _slideAnimation,
          isSubmitting: state.status == QuestionnaireStatus.submitting,
        );

      case QuestionnaireStatus.reviewing:
        return _ReviewView(
          key: const ValueKey('review'),
          state: state,
        );

      case QuestionnaireStatus.completed:
        return const _LoadingView(key: ValueKey('completed'));

      case QuestionnaireStatus.failed:
        return _ErrorView(
          key: const ValueKey('error'),
          message: state.errorMessage ?? 'შეცდომა მოხდა',
          onRetry: () {
            context.read<QuestionnaireCubit>().loadQuestionnaire(
              state.conversationId!,
            );
          },
        );
    }
  }
}

// ── Sub-views ─────────────────────────────────────────────────

class _LoadingView extends StatelessWidget {
  const _LoadingView({super.key});

  @override
  Widget build(BuildContext context) {
    return const Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          CircularProgressIndicator(),
          SizedBox(height: 20),
          Text(
            'კითხვების მომზადება...',
            style: TextStyle(fontSize: 16),
          ),
          SizedBox(height: 8),
          Text(
            'AI ქმნით თქვენი სიტუაციისთვის მორგებულ კითხვებს',
            style: TextStyle(fontSize: 13, color: Colors.grey),
            textAlign: TextAlign.center,
          ),
        ],
      ),
    );
  }
}

class _QuestionView extends StatefulWidget {
  final QuestionnaireState state;
  final AnimationController animController;
  final Animation<Offset> slideAnimation;
  final bool isSubmitting;

  const _QuestionView({
    super.key,
    required this.state,
    required this.animController,
    required this.slideAnimation,
    required this.isSubmitting,
  });

  @override
  State<_QuestionView> createState() => _QuestionViewState();
}

class _QuestionViewState extends State<_QuestionView> {
  String _currentAnswer = '';

  @override
  Widget build(BuildContext context) {
    final question = widget.state.currentQuestion;
    if (question == null) {
      return const _LoadingView();
    }

    final theme = Theme.of(context);
    final existingAnswer = widget.state.answers.firstWhere(
      (a) => a.questionId == question.id,
      orElse: () => const QuestionnaireAnswer(questionId: '', answer: ''),
    );
    final initialValue = existingAnswer.questionId.isNotEmpty
        ? existingAnswer.answer
        : null;

    return SlideTransition(
      position: widget.slideAnimation,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          QuestionnaireProgressIndicator(
            answered: widget.state.progress.answered,
            total: widget.state.progress.total,
            label: 'კითხვა ${widget.state.currentQuestionIndex + 1} / ${widget.state.questions.length}',
          ),
          const SizedBox(height: 24),
          Text(
            question.questionTextKa,
            style: theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
              height: 1.3,
            ),
          ),
          if (question.purpose.isNotEmpty) ...[
            const SizedBox(height: 6),
            Text(
              question.purpose,
              style: theme.textTheme.bodySmall?.copyWith(
                color: Colors.grey.shade600,
              ),
            ),
          ],
          const SizedBox(height: 20),
          Expanded(
            child: buildQuestionInput(
              question: question,
              initialValue: initialValue,
              onChanged: (v) => _currentAnswer = v,
            ),
          ),
          const SizedBox(height: 16),
          Row(
            children: [
              if (!question.required)
                TextButton.icon(
                  onPressed: widget.isSubmitting
                      ? null
                      : () => context.read<QuestionnaireCubit>().skipCurrentQuestion(),
                  icon: const Icon(Icons.skip_next_outlined),
                  label: const Text('გამოტოვება'),
                )
              else
                const Spacer(),
              const Spacer(),
              FilledButton.icon(
                onPressed: widget.isSubmitting
                    ? null
                    : () {
                        if (_validateAnswer(question, context)) {
                          context.read<QuestionnaireCubit>().submitAnswer(_currentAnswer);
                        }
                      },
                icon: widget.isSubmitting
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.arrow_forward),
                label: Text(widget.state.isLastQuestion ? 'დასრულება' : 'შემდეგი'),
              ),
            ],
          ),
          const SizedBox(height: 12),
        ],
      ),
    );
  }

  bool _validateAnswer(QuestionnaireQuestion question, BuildContext context) {
    if (question.required && _currentAnswer.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('გთხოვთ, შეავსოთ აუცილებელი ველი')),
      );
      return false;
    }
    return true;
  }
}

class _ReviewView extends StatelessWidget {
  final QuestionnaireState state;

  const _ReviewView({super.key, required this.state});

  @override
  Widget build(BuildContext context) {
    return ReviewSummary(
      questions: state.questions,
      answers: state.answers,
      onEdit: () {
        context.read<QuestionnaireCubit>().goBack();
      },
      onConfirm: () {
        context.read<QuestionnaireCubit>().finishQuestionnaire();
      },
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  final VoidCallback onRetry;

  const _ErrorView({
    super.key,
    required this.message,
    required this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          const Icon(Icons.error_outline, size: 48, color: Colors.red),
          const SizedBox(height: 16),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(fontSize: 16),
          ),
          const SizedBox(height: 20),
          FilledButton.icon(
            onPressed: onRetry,
            icon: const Icon(Icons.refresh),
            label: const Text('თავიდან ცდა'),
          ),
        ],
      ),
    );
  }
}
