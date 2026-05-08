import 'dart:async';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:themasteroflaw/src/src.dart';

// ---------------------------------------------------------------------------
// Models
// ---------------------------------------------------------------------------

class QuestionnaireQuestion {
  final String id;
  final String questionId;
  final String questionTextKa;
  final String questionType;
  final List<String> options;
  final bool required;
  final String purpose;
  final String legalRelevance;
  final int sortOrder;

  QuestionnaireQuestion({
    required this.id,
    required this.questionId,
    required this.questionTextKa,
    required this.questionType,
    required this.options,
    required this.required,
    required this.purpose,
    required this.legalRelevance,
    required this.sortOrder,
  });

  factory QuestionnaireQuestion.fromJson(Map<String, dynamic> json) {
    return QuestionnaireQuestion(
      id: json['id']?.toString() ?? '',
      questionId: json['question_id']?.toString() ?? '',
      questionTextKa: json['question_text_ka']?.toString() ?? '',
      questionType: json['question_type']?.toString() ?? 'text',
      options: (json['options'] as List<dynamic>?)?.map((e) => e.toString()).toList() ?? [],
      required: json['required'] as bool? ?? true,
      purpose: json['purpose']?.toString() ?? '',
      legalRelevance: json['legal_relevance']?.toString() ?? '',
      sortOrder: json['sort_order'] as int? ?? 0,
    );
  }
}

class QuestionnaireAnswer {
  final String questionId;
  final String answer;

  QuestionnaireAnswer({required this.questionId, required this.answer});
}

// ---------------------------------------------------------------------------
// Data Source
// ---------------------------------------------------------------------------

class QuestionnaireRemoteDataSource {
  final ThemasteroflawHttpClient _httpClient;

  QuestionnaireRemoteDataSource() : _httpClient = sl.get<ThemasteroflawHttpClient>();

  Uri _uri(String path) => Uri.parse(
    '${dotenv.env['API_BASE_URL'] ?? 'http://127.0.0.1:8000'}$path',
  );

  Future<Map<String, dynamic>> generateQuestionnaire({
    required String conversationId,
    required String domain,
    String context = '',
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/questionnaire/$conversationId/generate'),
      body: {
        'domain': domain,
        'context': context,
      },
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> getQuestionnaireState(String conversationId) async {
    final response = await _httpClient.get<Map<String, dynamic>>(
      _uri('/api/v1/questionnaire/$conversationId'),
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> submitAnswer({
    required String conversationId,
    required String questionId,
    required String answer,
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/questionnaire/$conversationId/answer'),
      body: {
        'question_id': questionId,
        'answer': answer,
      },
    );
    return response.data!;
  }

  Future<Map<String, dynamic>> skipQuestion({
    required String conversationId,
    required String questionId,
  }) async {
    final response = await _httpClient.post<Map<String, dynamic>>(
      _uri('/api/v1/questionnaire/$conversationId/skip'),
      body: {
        'question_id': questionId,
      },
    );
    return response.data!;
  }
}

// ---------------------------------------------------------------------------
// Cubit State
// ---------------------------------------------------------------------------

enum QuestionnaireStatus { initial, loading, ready, submitting, error, completed }

class QuestionnaireState {
  final QuestionnaireStatus status;
  final List<QuestionnaireQuestion> questions;
  final List<QuestionnaireAnswer> answers;
  final int currentIndex;
  final String? errorMessage;
  final int totalQuestions;
  final int answeredCount;

  const QuestionnaireState({
    this.status = QuestionnaireStatus.initial,
    this.questions = const [],
    this.answers = const [],
    this.currentIndex = 0,
    this.errorMessage,
    this.totalQuestions = 0,
    this.answeredCount = 0,
  });

  QuestionnaireState copyWith({
    QuestionnaireStatus? status,
    List<QuestionnaireQuestion>? questions,
    List<QuestionnaireAnswer>? answers,
    int? currentIndex,
    String? errorMessage,
    int? totalQuestions,
    int? answeredCount,
  }) {
    return QuestionnaireState(
      status: status ?? this.status,
      questions: questions ?? this.questions,
      answers: answers ?? this.answers,
      currentIndex: currentIndex ?? this.currentIndex,
      errorMessage: errorMessage ?? this.errorMessage,
      totalQuestions: totalQuestions ?? this.totalQuestions,
      answeredCount: answeredCount ?? this.answeredCount,
    );
  }

  /// Returns the current question or null if out of bounds.
  QuestionnaireQuestion? get currentQuestion =>
      (currentIndex >= 0 && currentIndex < questions.length) ? questions[currentIndex] : null;

  /// Returns the answer for a given questionId, if any.
  String? answerFor(String questionId) {
    try {
      return answers.firstWhere((a) => a.questionId == questionId).answer;
    } catch (_) {
      return null;
    }
  }

  /// True if the current question already has an answer stored locally.
  bool get hasCurrentAnswer =>
      currentQuestion != null && answerFor(currentQuestion!.questionId) != null;

  /// True if we can go back to a previous question.
  bool get canGoBack => currentIndex > 0;

  /// True if all required questions are answered.
  bool get isComplete {
    for (final q in questions) {
      if (q.required && answerFor(q.questionId) == null) return false;
    }
    return questions.isNotEmpty;
  }
}

// ---------------------------------------------------------------------------
// Cubit
// ---------------------------------------------------------------------------

class QuestionnaireCubit extends Cubit<QuestionnaireState> {
  final QuestionnaireRemoteDataSource _dataSource;

  QuestionnaireCubit({QuestionnaireRemoteDataSource? dataSource})
      : _dataSource = dataSource ?? QuestionnaireRemoteDataSource(),
        super(const QuestionnaireState());

  /// Start the questionnaire by generating questions for the conversation.
  Future<void> generateQuestionnaire({
    required String conversationId,
    required String domain,
    String context = '',
  }) async {
    emit(state.copyWith(status: QuestionnaireStatus.loading));
    try {
      final data = await _dataSource.generateQuestionnaire(
        conversationId: conversationId,
        domain: domain,
        context: context,
      );
      final rawQuestions = data['questions'] as List<dynamic>? ?? [];
      final questions = rawQuestions.map((q) => QuestionnaireQuestion.fromJson(q as Map<String, dynamic>)).toList();
      final total = data['total'] as int? ?? questions.length;

      emit(state.copyWith(
        status: QuestionnaireStatus.ready,
        questions: questions,
        totalQuestions: total,
        currentIndex: 0,
        answeredCount: 0,
      ));
    } catch (e) {
      emit(state.copyWith(status: QuestionnaireStatus.error, errorMessage: 'კითხვარის გენერაცია ვერ მოხერხდა'));
    }
  }

  /// Load existing questionnaire state (for resuming).
  Future<void> loadQuestionnaireState(String conversationId) async {
    emit(state.copyWith(status: QuestionnaireStatus.loading));
    try {
      final data = await _dataSource.getQuestionnaireState(conversationId);
      final rawQuestions = data['questions'] as List<dynamic>? ?? [];
      final questions = rawQuestions.map((q) => QuestionnaireQuestion.fromJson(q as Map<String, dynamic>)).toList();
      final rawAnswers = data['answers'] as List<dynamic>? ?? [];
      final answers = rawAnswers.map((a) {
        final map = a as Map<String, dynamic>;
        return QuestionnaireAnswer(
          questionId: map['question_id']?.toString() ?? '',
          answer: map['answer']?.toString() ?? '',
        );
      }).toList();
      final progress = data['progress'] as Map<String, dynamic>? ?? {};
      final answered = progress['answered'] as int? ?? answers.length;
      final total = progress['total'] as int? ?? questions.length;

      // Find first unanswered question
      int firstUnanswered = 0;
      for (int i = 0; i < questions.length; i++) {
        if (!answers.any((a) => a.questionId == questions[i].questionId)) {
          firstUnanswered = i;
          break;
        }
      }

      emit(state.copyWith(
        status: QuestionnaireStatus.ready,
        questions: questions,
        answers: answers,
        totalQuestions: total,
        answeredCount: answered,
        currentIndex: firstUnanswered,
      ));
    } catch (e) {
      emit(state.copyWith(status: QuestionnaireStatus.error, errorMessage: 'კითხვარის ჩატვირთვა ვერ მოხერხდა'));
    }
  }

  /// Submit an answer for the current question and advance.
  Future<void> submitAnswer({
    required String conversationId,
    required String questionId,
    required String answer,
  }) async {
    emit(state.copyWith(status: QuestionnaireStatus.submitting));
    try {
      final data = await _dataSource.submitAnswer(
        conversationId: conversationId,
        questionId: questionId,
        answer: answer,
      );

      // Update local answers
      final updatedAnswers = List<QuestionnaireAnswer>.from(state.answers);
      final existingIndex = updatedAnswers.indexWhere((a) => a.questionId == questionId);
      final newAnswer = QuestionnaireAnswer(questionId: questionId, answer: answer);
      if (existingIndex >= 0) {
        updatedAnswers[existingIndex] = newAnswer;
      } else {
        updatedAnswers.add(newAnswer);
      }

      // Merge follow-up questions if any
      final rawFollowUps = data['follow_ups'] as List<dynamic>? ?? [];
      final followUps = rawFollowUps.map((q) => QuestionnaireQuestion.fromJson(q as Map<String, dynamic>)).toList();
      final updatedQuestions = List<QuestionnaireQuestion>.from(state.questions);
      for (final fu in followUps) {
        if (!updatedQuestions.any((q) => q.questionId == fu.questionId)) {
          updatedQuestions.add(fu);
        }
      }

      final progress = data['progress'] as Map<String, dynamic>? ?? {};
      final answered = progress['answered'] as int? ?? updatedAnswers.length;
      final total = progress['total'] as int? ?? updatedQuestions.length;

      // Advance to next unanswered
      final nextIndex = _nextUnansweredIndex(updatedQuestions, updatedAnswers, state.currentIndex + 1);

      if (nextIndex == null || nextIndex >= updatedQuestions.length) {
        emit(state.copyWith(
          status: QuestionnaireStatus.completed,
          answers: updatedAnswers,
          questions: updatedQuestions,
          answeredCount: answered,
          totalQuestions: total,
        ));
      } else {
        emit(state.copyWith(
          status: QuestionnaireStatus.ready,
          answers: updatedAnswers,
          questions: updatedQuestions,
          currentIndex: nextIndex,
          answeredCount: answered,
          totalQuestions: total,
        ));
      }
    } catch (e) {
      emit(state.copyWith(
        status: QuestionnaireStatus.error,
        errorMessage: 'პასუხის გაგზავნა ვერ მოხერხდა',
      ));
    }
  }

  /// Skip the current question (only if not required).
  Future<void> skipQuestion({
    required String conversationId,
    required String questionId,
  }) async {
    emit(state.copyWith(status: QuestionnaireStatus.submitting));
    try {
      final data = await _dataSource.skipQuestion(
        conversationId: conversationId,
        questionId: questionId,
      );

      final progress = data['progress'] as Map<String, dynamic>? ?? {};
      final answered = progress['answered'] as int? ?? state.answeredCount + 1;
      final total = progress['total'] as int? ?? state.totalQuestions;

      // Mark as skipped locally with empty answer
      final updatedAnswers = List<QuestionnaireAnswer>.from(state.answers);
      if (!updatedAnswers.any((a) => a.questionId == questionId)) {
        updatedAnswers.add(QuestionnaireAnswer(questionId: questionId, answer: ''));
      }

      final nextIndex = _nextUnansweredIndex(state.questions, updatedAnswers, state.currentIndex + 1);

      if (nextIndex == null || nextIndex >= state.questions.length) {
        emit(state.copyWith(
          status: QuestionnaireStatus.completed,
          answers: updatedAnswers,
          answeredCount: answered,
          totalQuestions: total,
        ));
      } else {
        emit(state.copyWith(
          status: QuestionnaireStatus.ready,
          answers: updatedAnswers,
          currentIndex: nextIndex,
          answeredCount: answered,
          totalQuestions: total,
        ));
      }
    } catch (e) {
      emit(state.copyWith(
        status: QuestionnaireStatus.error,
        errorMessage: 'შეკითხვის გამოტოვება ვერ მოხერხდა',
      ));
    }
  }

  /// Go back to the previous question.
  void goBack() {
    if (state.currentIndex > 0) {
      emit(state.copyWith(currentIndex: state.currentIndex - 1));
    }
  }

  /// Jump to a specific question index (used in review mode).
  void jumpToQuestion(int index) {
    if (index >= 0 && index < state.questions.length) {
      emit(state.copyWith(
        status: QuestionnaireStatus.ready,
        currentIndex: index,
      ));
    }
  }

  /// Finish questionnaire and go to review.
  void finish() {
    emit(state.copyWith(status: QuestionnaireStatus.completed));
  }

  int? _nextUnansweredIndex(
    List<QuestionnaireQuestion> questions,
    List<QuestionnaireAnswer> answers,
    int startFrom,
  ) {
    for (int i = startFrom; i < questions.length; i++) {
      if (!answers.any((a) => a.questionId == questions[i].questionId)) {
        return i;
      }
    }
    // Also check before startFrom (in case follow-ups were inserted)
    for (int i = 0; i < startFrom && i < questions.length; i++) {
      if (!answers.any((a) => a.questionId == questions[i].questionId)) {
        return i;
      }
    }
    return null;
  }
}
