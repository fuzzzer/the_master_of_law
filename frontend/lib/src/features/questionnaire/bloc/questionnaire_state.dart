part of 'questionnaire_cubit.dart';

/// Status of the questionnaire flow.
enum QuestionnaireStatus {
  initial,
  generating,      // waiting for AI to generate questions
  loading,         // fetching existing questionnaire
  answering,       // showing a question
  submitting,      // sending answer to backend
  reviewing,       // showing answer summary
  completed,       // all questions answered
  failed,
}

/// State for the dynamic questionnaire flow.
class QuestionnaireState {
  final QuestionnaireStatus status;
  final String? conversationId;
  final List<QuestionnaireQuestion> questions;
  final List<QuestionnaireAnswer> answers;
  final int currentQuestionIndex;
  final QuestionnaireProgress progress;
  final String? errorMessage;
  final bool canGoBack;

  const QuestionnaireState({
    this.status = QuestionnaireStatus.initial,
    this.conversationId,
    this.questions = const [],
    this.answers = const [],
    this.currentQuestionIndex = 0,
    this.progress = const QuestionnaireProgress(answered: 0, total: 0),
    this.errorMessage,
    this.canGoBack = false,
  });

  QuestionnaireQuestion? get currentQuestion =>
      (questions.isNotEmpty && currentQuestionIndex < questions.length)
          ? questions[currentQuestionIndex]
          : null;

  bool get isLastQuestion =>
      currentQuestionIndex >= questions.length - 1 &&
      questions.isNotEmpty;

  QuestionnaireState copyWith({
    QuestionnaireStatus? status,
    String? conversationId,
    List<QuestionnaireQuestion>? questions,
    List<QuestionnaireAnswer>? answers,
    int? currentQuestionIndex,
    QuestionnaireProgress? progress,
    String? errorMessage,
    bool? canGoBack,
  }) {
    return QuestionnaireState(
      status: status ?? this.status,
      conversationId: conversationId ?? this.conversationId,
      questions: questions ?? this.questions,
      answers: answers ?? this.answers,
      currentQuestionIndex: currentQuestionIndex ?? this.currentQuestionIndex,
      progress: progress ?? this.progress,
      errorMessage: errorMessage,
      canGoBack: canGoBack ?? this.canGoBack,
    );
  }
}
