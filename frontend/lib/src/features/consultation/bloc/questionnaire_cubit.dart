import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';

part 'questionnaire_state.dart';

class QuestionnaireCubit extends Cubit<QuestionnaireState> {
  final QuestionnaireRepository _repository;

  QuestionnaireCubit({required QuestionnaireRepository repository})
    : _repository = repository,
      super(const QuestionnaireState());

  Future<void> generateQuestionnaire({
    required String conversationId,
    required String domain,
    required String userDescription,
  }) async {
    emit(
      state.copyWith(
        status: StateStatus.loading,
        conversationId: conversationId,
      ),
    );

    final result = await _repository.generateQuestionnaire(
      conversationId: conversationId,
      domain: domain,
      userDescription: userDescription,
    );

    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        final rawQuestions = data['questions'] as List<dynamic>? ?? [];
        final questions = rawQuestions
            .map(
              (q) => QuestionnaireQuestionModel.fromJson(
                q as Map<String, dynamic>,
              ),
            )
            .toList();
        emit(
          state.copyWith(
            status: StateStatus.success,
            questions: questions,
            currentIndex: 0,
            answers: {},
          ),
        );
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        emit(state.copyWith(status: StateStatus.failed, failureType: type));
    }
  }

  Future<void> loadQuestionnaire(String conversationId) async {
    emit(
      state.copyWith(
        status: StateStatus.loading,
        conversationId: conversationId,
      ),
    );

    final result = await _repository.getQuestionnaire(conversationId);
    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        final rawQuestions = data['questions'] as List<dynamic>? ?? [];
        final rawAnswers = data['answers'] as List<dynamic>? ?? [];
        final questions = rawQuestions
            .map(
              (q) => QuestionnaireQuestionModel.fromJson(
                q as Map<String, dynamic>,
              ),
            )
            .toList();
        final answers = <String, String>{};
        for (final a in rawAnswers) {
          final map = a as Map<String, dynamic>;
          if (map['skipped'] != true && map['answer_value'] != null) {
            answers[map['question_id'].toString()] = map['answer_value']
                .toString();
          }
        }
        final currentIndex = answers.length < questions.length
            ? answers.length
            : questions.length - 1;
        emit(
          state.copyWith(
            status: StateStatus.success,
            questions: questions,
            answers: answers,
            currentIndex: currentIndex,
          ),
        );
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        emit(state.copyWith(status: StateStatus.failed, failureType: type));
    }
  }

  Future<void> submitAnswer(String answer) async {
    if (state.conversationId == null || state.currentQuestion == null) return;
    final question = state.currentQuestion!;

    emit(state.copyWith(isSubmitting: true));

    final result = await _repository.submitAnswer(
      conversationId: state.conversationId!,
      questionId: question.questionId,
      answer: answer,
    );

    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        final newAnswers = Map<String, String>.from(state.answers);
        newAnswers[question.questionId] = answer;

        final hasNext = data['next_question'] != null;
        final nextIndex = hasNext ? state.currentIndex + 1 : state.currentIndex;

        emit(
          state.copyWith(
            isSubmitting: false,
            answers: newAnswers,
            currentIndex: nextIndex,
            isComplete: !hasNext,
          ),
        );
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        emit(state.copyWith(isSubmitting: false, failureType: type));
    }
  }

  Future<void> skipRemaining() async {
    if (state.conversationId == null) return;
    emit(state.copyWith(isSubmitting: true));

    final result = await _repository.skipRemaining(state.conversationId!);
    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        emit(
          state.copyWith(
            isSubmitting: false,
            isComplete: data['ready_for_analysis'] as bool? ?? true,
          ),
        );
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        emit(state.copyWith(isSubmitting: false, failureType: type));
    }
  }

  Future<void> extractFromNarrative({
    required String conversationId,
    required String domain,
    required String narrative,
  }) async {
    emit(
      state.copyWith(
        status: StateStatus.loading,
        conversationId: conversationId,
      ),
    );

    final result = await _repository.extractFromNarrative(
      conversationId: conversationId,
      domain: domain,
      narrative: narrative,
    );

    switch (result) {
      case ConsultationSuccess<Map<String, dynamic>>(:final data):
        final extractedCount = data['extracted_count'] as int? ?? 0;
        final totalQuestions = data['total_questions'] as int? ?? 0;
        emit(
          state.copyWith(
            status: StateStatus.success,
            isComplete: true,
            extractedCount: extractedCount,
            totalQuestions: totalQuestions,
          ),
        );
      case ConsultationFailure<Map<String, dynamic>>(:final type):
        emit(state.copyWith(status: StateStatus.failed, failureType: type));
    }
  }

  void goToPreviousQuestion() {
    if (state.currentIndex > 0) {
      emit(state.copyWith(currentIndex: state.currentIndex - 1));
    }
  }

  void goToNextQuestion() {
    if (state.currentIndex < state.questions.length - 1) {
      emit(state.copyWith(currentIndex: state.currentIndex + 1));
    }
  }
}
