import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

part 'questionnaire_state.dart';

/// Manages the dynamic questionnaire flow: generation, answering, review.
class QuestionnaireCubit extends Cubit<QuestionnaireState> {
  final QuestionnaireRepository _repository;

  QuestionnaireCubit({required QuestionnaireRepository repository})
      : _repository = repository,
        super(const QuestionnaireState());

  /// Start the questionnaire by generating questions for a conversation.
  Future<void> startQuestionnaire({
    required String conversationId,
    required String domain,
    String context = '',
  }) async {
    emit(state.copyWith(
      status: QuestionnaireStatus.generating,
      conversationId: conversationId,
    ));

    final result = await _repository.generateQuestionnaire(
      conversationId: conversationId,
      domain: domain,
      context: context,
    );

    switch (result) {
      case QuestionnaireSuccess<Map<String, dynamic>>(:final data):
        final rawQuestions = data['questions'] as List<dynamic>? ?? [];
        final questions = rawQuestions
            .map((q) => QuestionnaireQuestion.fromJson(q as Map<String, dynamic>))
            .toList();
        final total = data['total'] as int? ?? questions.length;

        emit(state.copyWith(
          status: QuestionnaireStatus.answering,
          questions: questions,
          progress: QuestionnaireProgress(answered: 0, total: total),
          currentQuestionIndex: 0,
          canGoBack: false,
        ));

      case QuestionnaireFailure<Map<String, dynamic>>(:final type):
        emit(state.copyWith(
          status: QuestionnaireStatus.failed,
          errorMessage: type.name,
        ));
    }
  }

  /// Load an existing questionnaire state from the backend.
  Future<void> loadQuestionnaire(String conversationId) async {
    emit(state.copyWith(
      status: QuestionnaireStatus.loading,
      conversationId: conversationId,
    ));

    final result = await _repository.getQuestionnaire(conversationId);

    switch (result) {
      case QuestionnaireSuccess<Map<String, dynamic>>(:final data):
        final rawQuestions = data['questions'] as List<dynamic>? ?? [];
        final rawAnswers = data['answers'] as List<dynamic>? ?? [];
        final progress = QuestionnaireProgress.fromJson(
          data['progress'] as Map<String, dynamic>? ?? {},
        );

        final questions = rawQuestions
            .map((q) => QuestionnaireQuestion.fromJson(q as Map<String, dynamic>))
            .toList();
        final answers = rawAnswers
            .map((a) => QuestionnaireAnswer(
                  questionId: (a as Map<String, dynamic>)['question_id']?.toString() ?? '',
                  answer: a['answer']?.toString() ?? '',
                ))
            .toList();

        var index = 0;
        for (var i = 0; i < questions.length; i++) {
          final hasAnswer = answers.any((a) => a.questionId == questions[i].id);
          if (!hasAnswer && !questions[i].skipped) {
            index = i;
            break;
          }
          if (i == questions.length - 1) {
            index = questions.length;
          }
        }

        final isComplete = index >= questions.length;
        emit(state.copyWith(
          status: isComplete ? QuestionnaireStatus.reviewing : QuestionnaireStatus.answering,
          questions: questions,
          answers: answers,
          progress: progress,
          currentQuestionIndex: index.clamp(0, questions.length),
          canGoBack: index > 0,
        ));

      case QuestionnaireFailure<Map<String, dynamic>>(:final type):
        emit(state.copyWith(
          status: QuestionnaireStatus.failed,
          errorMessage: type.name,
        ));
    }
  }

  /// Submit an answer for the current question and advance.
  Future<void> submitAnswer(String answer) async {
    final current = state.currentQuestion;
    if (current == null || state.conversationId == null) return;

    emit(state.copyWith(status: QuestionnaireStatus.submitting));

    final result = await _repository.submitAnswer(
      conversationId: state.conversationId!,
      questionId: current.id,
      answer: answer,
    );

    switch (result) {
      case QuestionnaireSuccess<Map<String, dynamic>>(:final data):
        final progress = QuestionnaireProgress.fromJson(
          data['progress'] as Map<String, dynamic>? ?? {},
        );
        final nextQuestion = data['next_question'] as Map<String, dynamic>?;
        final rawFollowUps = data['follow_ups'] as List<dynamic>? ?? [];

        final newAnswers = [
          ...state.answers,
          QuestionnaireAnswer(questionId: current.id, answer: answer),
        ];

        final followUpQuestions = rawFollowUps
            .map((q) => QuestionnaireQuestion.fromJson(q as Map<String, dynamic>))
            .toList();
        final updatedQuestions = [...state.questions, ...followUpQuestions];

        if (nextQuestion != null) {
          final nextId = nextQuestion['question_id']?.toString() ?? nextQuestion['id']?.toString() ?? '';
          final nextIndex = updatedQuestions.indexWhere((q) => q.id == nextId);
          emit(state.copyWith(
            status: QuestionnaireStatus.answering,
            questions: updatedQuestions,
            answers: newAnswers,
            progress: progress,
            currentQuestionIndex: nextIndex >= 0 ? nextIndex : state.currentQuestionIndex + 1,
            canGoBack: true,
          ));
        } else {
          emit(state.copyWith(
            status: QuestionnaireStatus.reviewing,
            questions: updatedQuestions,
            answers: newAnswers,
            progress: progress,
            currentQuestionIndex: updatedQuestions.length,
            canGoBack: true,
          ));
        }

      case QuestionnaireFailure<Map<String, dynamic>>(:final type):
        emit(state.copyWith(
          status: QuestionnaireStatus.failed,
          errorMessage: type.name,
        ));
    }
  }

  /// Skip the current question (only if not required).
  Future<void> skipCurrentQuestion() async {
    final current = state.currentQuestion;
    if (current == null || state.conversationId == null || current.required) return;

    emit(state.copyWith(status: QuestionnaireStatus.submitting));

    final result = await _repository.skipQuestion(
      conversationId: state.conversationId!,
      questionId: current.id,
    );

    switch (result) {
      case QuestionnaireSuccess<Map<String, dynamic>>(:final data):
        final progress = QuestionnaireProgress.fromJson(
          data['progress'] as Map<String, dynamic>? ?? {},
        );
        final ready = data['ready_for_analysis'] == true;

        final updatedQuestions = [...state.questions];
        final idx = updatedQuestions.indexWhere((q) => q.id == current.id);
        if (idx >= 0) {
          updatedQuestions[idx] = updatedQuestions[idx].copyWith(skipped: true);
        }

        if (ready || state.currentQuestionIndex >= updatedQuestions.length - 1) {
          emit(state.copyWith(
            status: QuestionnaireStatus.reviewing,
            questions: updatedQuestions,
            progress: progress,
            currentQuestionIndex: updatedQuestions.length,
            canGoBack: true,
          ));
        } else {
          emit(state.copyWith(
            status: QuestionnaireStatus.answering,
            questions: updatedQuestions,
            progress: progress,
            currentQuestionIndex: state.currentQuestionIndex + 1,
            canGoBack: true,
          ));
        }

      case QuestionnaireFailure<Map<String, dynamic>>(:final type):
        emit(state.copyWith(
          status: QuestionnaireStatus.failed,
          errorMessage: type.name,
        ));
    }
  }

  /// Go back to the previous question for editing.
  void goBack() {
    if (!state.canGoBack || state.currentQuestionIndex <= 0) return;
    emit(state.copyWith(
      status: QuestionnaireStatus.answering,
      currentQuestionIndex: state.currentQuestionIndex - 1,
      canGoBack: state.currentQuestionIndex - 1 > 0,
    ));
  }

  /// Move from review screen to the next phase (analysis).
  void finishQuestionnaire() {
    emit(state.copyWith(status: QuestionnaireStatus.completed));
  }
}
