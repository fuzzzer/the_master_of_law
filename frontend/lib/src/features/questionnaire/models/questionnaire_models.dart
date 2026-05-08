/// Questionnaire question model from backend.
class QuestionnaireQuestion {
  final String id;
  final String questionTextKa;
  final String questionType; // text, boolean, choice, date, number
  final List<String> options;
  final bool required;
  final String purpose;
  final String legalRelevance;
  final int sortOrder;
  final String? answerValue;
  final bool skipped;

  const QuestionnaireQuestion({
    required this.id,
    required this.questionTextKa,
    required this.questionType,
    this.options = const [],
    this.required = true,
    this.purpose = '',
    this.legalRelevance = '',
    this.sortOrder = 0,
    this.answerValue,
    this.skipped = false,
  });

  factory QuestionnaireQuestion.fromJson(Map<String, dynamic> json) {
    return QuestionnaireQuestion(
      id: json['question_id']?.toString() ?? json['id']?.toString() ?? '',
      questionTextKa: json['question_text_ka']?.toString() ?? '',
      questionType: json['question_type']?.toString() ?? 'text',
      options: (json['options'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      required: json['required'] == true,
      purpose: json['purpose']?.toString() ?? '',
      legalRelevance: json['legal_relevance']?.toString() ?? '',
      sortOrder: (json['sort_order'] as int?) ?? 0,
      answerValue: json['answer_value']?.toString(),
      skipped: json['skipped'] == true,
    );
  }

  QuestionnaireQuestion copyWith({
    String? answerValue,
    bool? skipped,
  }) {
    return QuestionnaireQuestion(
      id: id,
      questionTextKa: questionTextKa,
      questionType: questionType,
      options: options,
      required: required,
      purpose: purpose,
      legalRelevance: legalRelevance,
      sortOrder: sortOrder,
      answerValue: answerValue ?? this.answerValue,
      skipped: skipped ?? this.skipped,
    );
  }
}

/// User answer to a single question.
class QuestionnaireAnswer {
  final String questionId;
  final String answer;

  const QuestionnaireAnswer({
    required this.questionId,
    required this.answer,
  });

  Map<String, dynamic> toJson() => {
        'question_id': questionId,
        'answer': answer,
      };
}

/// Progress through the questionnaire.
class QuestionnaireProgress {
  final int answered;
  final int total;

  const QuestionnaireProgress({required this.answered, required this.total});

  factory QuestionnaireProgress.fromJson(Map<String, dynamic> json) {
    return QuestionnaireProgress(
      answered: (json['answered'] as int?) ?? 0,
      total: (json['total'] as int?) ?? 0,
    );
  }

  double get fraction => total == 0 ? 0.0 : answered / total;
  String get labelKa => '$answered / $total კითხვა';
}
