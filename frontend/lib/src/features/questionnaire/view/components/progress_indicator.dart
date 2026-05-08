import 'package:flutter/material.dart';

/// Linear progress indicator for the questionnaire flow.
class QuestionnaireProgressIndicator extends StatelessWidget {
  final int answered;
  final int total;
  final String label;

  const QuestionnaireProgressIndicator({
    super.key,
    required this.answered,
    required this.total,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    final fraction = total == 0 ? 0.0 : answered / total;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              label,
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.w500,
                  ),
            ),
            Text(
              '$answered / $total',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                    fontWeight: FontWeight.w600,
                  ),
            ),
          ],
        ),
        const SizedBox(height: 6),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: LinearProgressIndicator(
            value: fraction,
            minHeight: 8,
            backgroundColor: Colors.grey.shade200,
            valueColor: AlwaysStoppedAnimation<Color>(
              Theme.of(context).colorScheme.primary,
            ),
          ),
        ),
      ],
    );
  }
}
