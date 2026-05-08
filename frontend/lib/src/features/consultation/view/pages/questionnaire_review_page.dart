import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/src.dart';

class QuestionnaireReviewPage extends StatelessWidget {
  final List<QuestionnaireQuestionModel> questions;
  final Map<String, String> answers;
  final VoidCallback onConfirm;
  final VoidCallback onEdit;

  const QuestionnaireReviewPage({
    super.key,
    required this.questions,
    required this.answers,
    required this.onConfirm,
    required this.onEdit,
  });

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'პასუხების მიმოხილვა',
          style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
        ),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: onEdit,
        ),
      ),
      body: ListView.separated(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        itemCount: questions.length + 1,
        separatorBuilder: (_, __) => Divider(
          color: uiColors.secondaryTextColor.withValues(alpha: 0.1),
          height: 1,
        ),
        itemBuilder: (context, index) {
          if (index == 0) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'გადახედეთ თქვენს პასუხებს',
                    style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'დარწმუნდით, რომ ინფორმაცია სწორია, სანამ ანალიზს დაიწყებთ.',
                    style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                  ),
                ],
              ),
            );
          }

          final question = questions[index - 1];
          final answer = answers[question.questionId];
          final isAnswered = answer != null && answer.isNotEmpty;

          return Padding(
            padding: const EdgeInsets.symmetric(vertical: 12),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  width: 24,
                  height: 24,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: isAnswered
                        ? uiColors.accentColor.withValues(alpha: 0.15)
                        : uiColors.secondaryTextColor.withValues(alpha: 0.1),
                  ),
                  child: Center(
                    child: Text(
                      '$index',
                      style: uiTextStyles.caption11.copyWith(
                        color: isAnswered ? uiColors.accentColor : uiColors.secondaryTextColor,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        question.questionText,
                        style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        isAnswered ? _formatAnswer(answer, question.questionType) : 'გამოტოვებულია',
                        style: uiTextStyles.body14.copyWith(
                          color: isAnswered ? uiColors.primaryTextColor : uiColors.secondaryTextColor,
                          fontStyle: isAnswered ? FontStyle.normal : FontStyle.italic,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        },
      ),
      bottomNavigationBar: Container(
        padding: EdgeInsets.fromLTRB(20, 12, 20, MediaQuery.of(context).padding.bottom + 12),
        decoration: BoxDecoration(
          color: uiColors.backgroundSecondaryColor,
          border: Border(top: BorderSide(color: uiColors.secondaryTextColor.withValues(alpha: 0.1))),
        ),
        child: Row(
          children: [
            Expanded(
              child: OutlinedButton(
                onPressed: onEdit,
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  side: BorderSide(color: uiColors.secondaryTextColor.withValues(alpha: 0.3)),
                ),
                child: Text(
                  'რედაქტირება',
                  style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
                ),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              flex: 2,
              child: ElevatedButton(
                onPressed: onConfirm,
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                ),
                child: Text(
                  'ანალიზის დაწყება',
                  style: uiTextStyles.bodyBold14,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  String _formatAnswer(String answer, String questionType) {
    if (questionType == 'date') {
      final date = DateTime.tryParse(answer);
      if (date != null) {
        return '${date.day.toString().padLeft(2, '0')}/${date.month.toString().padLeft(2, '0')}/${date.year}';
      }
    }
    return answer;
  }
}
