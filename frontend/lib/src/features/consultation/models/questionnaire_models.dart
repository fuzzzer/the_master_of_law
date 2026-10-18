/// Questionnaire question model.
class QuestionnaireQuestionModel {
  final String questionId;
  final String questionText;
  final String questionType;
  final List<String>? options;
  final bool required;
  final String? purpose;
  final String? legalRelevance;

  const QuestionnaireQuestionModel({
    required this.questionId,
    required this.questionText,
    this.questionType = 'text',
    this.options,
    this.required = true,
    this.purpose,
    this.legalRelevance,
  });

  factory QuestionnaireQuestionModel.fromJson(Map<String, dynamic> json) {
    return QuestionnaireQuestionModel(
      questionId: json['question_id']?.toString() ?? '',
      questionText: json['question_text']?.toString() ?? '',
      questionType: json['question_type']?.toString() ?? 'text',
      options: (json['options'] as List?)?.map((e) => e.toString()).toList(),
      required: json['required'] as bool? ?? true,
      purpose: json['purpose']?.toString(),
      legalRelevance: json['legal_relevance']?.toString(),
    );
  }
}

/// Questionnaire answer model.
class QuestionnaireAnswerModel {
  final String questionId;
  final String answerValue;
  final String answerType;
  final bool skipped;

  const QuestionnaireAnswerModel({
    required this.questionId,
    required this.answerValue,
    this.answerType = 'text',
    this.skipped = false,
  });

  factory QuestionnaireAnswerModel.fromJson(Map<String, dynamic> json) {
    return QuestionnaireAnswerModel(
      questionId: json['question_id']?.toString() ?? '',
      answerValue: json['answer_value']?.toString() ?? '',
      answerType: json['answer_type']?.toString() ?? 'text',
      skipped: json['skipped'] as bool? ?? false,
    );
  }
}

/// Progress tracking for the questionnaire.
class QuestionnaireProgress {
  final int answered;
  final int skipped;
  final int total;
  final int remaining;

  const QuestionnaireProgress({
    this.answered = 0,
    this.skipped = 0,
    this.total = 0,
    this.remaining = 0,
  });

  factory QuestionnaireProgress.fromJson(Map<String, dynamic> json) {
    return QuestionnaireProgress(
      answered: json['answered'] as int? ?? 0,
      skipped: json['skipped'] as int? ?? 0,
      total: json['total'] as int? ?? 0,
      remaining: json['remaining'] as int? ?? 0,
    );
  }
}
