part of 'questionnaire_cubit.dart';

class QuestionnaireState {
  final StateStatus status;
  final String? conversationId;
  final List<QuestionnaireQuestionModel> questions;
  final Map<String, String> answers;
  final int currentIndex;
  final bool isSubmitting;
  final bool isComplete;
  final int extractedCount;
  final int totalQuestions;
  final ConsultationFailureType? failureType;

  const QuestionnaireState({
    this.status = StateStatus.initial,
    this.conversationId,
    this.questions = const [],
    this.answers = const {},
    this.currentIndex = 0,
    this.isSubmitting = false,
    this.isComplete = false,
    this.extractedCount = 0,
    this.totalQuestions = 0,
    this.failureType,
  });

  QuestionnaireQuestionModel? get currentQuestion =>
      currentIndex < questions.length ? questions[currentIndex] : null;

  bool get isLastQuestion => currentIndex >= questions.length - 1;

  bool get isFirstQuestion => currentIndex == 0;

  int get answeredCount => answers.length;

  String? get currentAnswer =>
      currentQuestion != null ? answers[currentQuestion!.questionId] : null;

  bool get hasUnansweredRequired =>
      questions.any((q) => q.required && !answers.containsKey(q.questionId));

  QuestionnaireState copyWith({
    StateStatus? status,
    String? conversationId,
    List<QuestionnaireQuestionModel>? questions,
    Map<String, String>? answers,
    int? currentIndex,
    bool? isSubmitting,
    bool? isComplete,
    int? extractedCount,
    int? totalQuestions,
    ConsultationFailureType? failureType,
  }) {
    return QuestionnaireState(
      status: status ?? this.status,
      conversationId: conversationId ?? this.conversationId,
      questions: questions ?? this.questions,
      answers: answers ?? this.answers,
      currentIndex: currentIndex ?? this.currentIndex,
      isSubmitting: isSubmitting ?? this.isSubmitting,
      isComplete: isComplete ?? this.isComplete,
      extractedCount: extractedCount ?? this.extractedCount,
      totalQuestions: totalQuestions ?? this.totalQuestions,
      failureType: failureType ?? this.failureType,
    );
  }
}
