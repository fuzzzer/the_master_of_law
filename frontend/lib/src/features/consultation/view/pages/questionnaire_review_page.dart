import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
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
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    return Scaffold(
      appBar: AppBar(
        // Title style comes from appBarTheme (titleM + ink), built from roles.
        title: const Text('პასუხების მიმოხილვა'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: onEdit,
        ),
      ),
      body: ListView.separated(
        padding: density.screen.copyWith(top: space.l, bottom: space.l),
        itemCount: questions.length + 1,
        // Divider colour and thickness come from dividerTheme (line, 1px).
        separatorBuilder: (_, __) => const Divider(),
        itemBuilder: (context, index) {
          if (index == 0) {
            return Padding(
              padding: EdgeInsets.only(bottom: space.l),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'გადახედეთ თქვენს პასუხებს',
                    style: type.titleM.copyWith(color: colors.ink),
                  ),
                  SizedBox(height: space.xs),
                  Text(
                    'დარწმუნდით, რომ ინფორმაცია სწორია, სანამ ანალიზს დაიწყებთ.',
                    style: type.body.copyWith(color: colors.inkMute),
                  ),
                ],
              ),
            );
          }

          final question = questions[index - 1];
          final answer = answers[question.questionId];
          final isAnswered = answer != null && answer.isNotEmpty;

          return Padding(
            padding: EdgeInsets.symmetric(vertical: space.m),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Container(
                  // Dimensions: the step marker's fixed footprint.
                  width: 24,
                  height: 24,
                  decoration: BoxDecoration(
                    // The kit's "on" state is INVERTED-MONO, not an accent
                    // tint (inputs/fuzzzy_filter_chip.dart:92-104).
                    color: isAnswered ? colors.actionPrimaryBg : colors.surface,
                    border: Border.all(
                      color: isAnswered ? colors.actionPrimaryBg : colors.line,
                    ),
                    borderRadius: BorderRadius.circular(radius.circle),
                  ),
                  child: Center(
                    child: Text(
                      '$index',
                      // `control` IS the w600 role — no fontWeight override.
                      style: type.control.copyWith(
                        color: isAnswered
                            ? colors.actionPrimaryFg
                            : colors.inkMute,
                      ),
                    ),
                  ),
                ),
                SizedBox(width: space.m),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        question.questionText,
                        style: type.titleS.copyWith(color: colors.ink),
                      ),
                      SizedBox(height: space.xs),
                      Text(
                        isAnswered ? _formatAnswer(answer, question.questionType) : 'გამოტოვებულია',
                        // Italic is not a role, and Ink has no italic face.
                        // "Skipped" is a PLACEHOLDER, which is exactly what
                        // `inkFaint` is for (USING §2.2).
                        style: type.body.copyWith(
                          color: isAnswered ? colors.ink : colors.inkFaint,
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
        padding: EdgeInsets.fromLTRB(
          density.screen.left,
          space.m,
          density.screen.right,
          MediaQuery.of(context).padding.bottom + space.m,
        ),
        decoration: BoxDecoration(
          color: colors.surface,
          border: Border(top: BorderSide(color: colors.line)),
        ),
        child: Row(
          children: [
            Expanded(
              // `FuzzzyButton.secondary` (buttons/fuzzzy_button.dart:99-100):
              // `ink` label on a `lineStrong` outline, no fill.
              child: OutlinedButton(
                onPressed: onEdit,
                style: OutlinedButton.styleFrom(
                  padding: density.snug,
                  side: BorderSide(color: colors.lineStrong),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(radius.m),
                  ),
                ),
                child: Text(
                  'რედაქტირება',
                  style: type.control.copyWith(color: colors.ink),
                ),
              ),
            ),
            SizedBox(width: space.m),
            Expanded(
              flex: 2,
              // `FuzzzyButton.primary`: the actionPrimary pair, radius.m,
              // `control` label. The fork left this to Material's defaults.
              child: ElevatedButton(
                onPressed: onConfirm,
                style: ElevatedButton.styleFrom(
                  backgroundColor: colors.actionPrimaryBg,
                  foregroundColor: colors.actionPrimaryFg,
                  padding: density.snug,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(radius.m),
                  ),
                ),
                child: Text(
                  'ანალიზის დაწყება',
                  style: type.control.copyWith(color: colors.actionPrimaryFg),
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
