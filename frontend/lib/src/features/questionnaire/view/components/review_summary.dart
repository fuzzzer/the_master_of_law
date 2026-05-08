import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/src.dart';

/// Review screen showing all answered questions in a summary card.
class ReviewSummary extends StatelessWidget {
  final List<QuestionnaireQuestion> questions;
  final List<QuestionnaireAnswer> answers;
  final VoidCallback onEdit;
  final VoidCallback onConfirm;

  const ReviewSummary({
    super.key,
    required this.questions,
    required this.answers,
    required this.onEdit,
    required this.onConfirm,
  });

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'შეამოწმეთ თქვენი პასუხები',
          style: theme.textTheme.headlineSmall?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          'გთხოვთ, გადაამოწმოთ პასუხები ანალიზის დაწყებამდე.',
          style: theme.textTheme.bodyMedium?.copyWith(
            color: Colors.grey.shade600,
          ),
        ),
        const SizedBox(height: 20),
        Expanded(
          child: ListView.builder(
            itemCount: questions.length,
            itemBuilder: (context, index) {
              final q = questions[index];
              final answer = answers.firstWhere(
                (a) => a.questionId == q.id,
                orElse: () => const QuestionnaireAnswer(questionId: '', answer: ''),
              );
              if (answer.questionId.isEmpty && !q.skipped) {
                return const SizedBox.shrink();
              }
              return _AnswerCard(
                question: q,
                answer: answer.answer,
                skipped: q.skipped,
                onTap: onEdit,
              );
            },
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          child: FilledButton.icon(
            onPressed: onConfirm,
            icon: const Icon(Icons.check_circle_outline),
            label: const Text(
              'დაადასტურეთ და გააგრძელეთ',
              style: TextStyle(fontSize: 16),
            ),
          ),
        ),
      ],
    );
  }
}

class _AnswerCard extends StatelessWidget {
  final QuestionnaireQuestion question;
  final String answer;
  final bool skipped;
  final VoidCallback onTap;

  const _AnswerCard({
    required this.question,
    required this.answer,
    required this.skipped,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              question.questionTextKa,
              style: const TextStyle(
                fontWeight: FontWeight.w600,
                fontSize: 14,
              ),
            ),
            const SizedBox(height: 6),
            if (skipped)
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.grey.shade200,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  'გამოტოვებულია',
                  style: TextStyle(
                    color: Colors.grey.shade600,
                    fontSize: 13,
                    fontStyle: FontStyle.italic,
                  ),
                ),
              )
            else
              Text(
                answer,
                style: const TextStyle(fontSize: 15),
              ),
            if (question.purpose.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                question.purpose,
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey.shade500,
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
