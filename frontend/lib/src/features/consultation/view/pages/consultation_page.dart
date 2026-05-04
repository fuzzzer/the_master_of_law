import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/core/core.dart';

/// Standalone consultation page (accessible from Laws tab).
/// Full implementation in Step 4.
class ConsultationPage extends StatelessWidget {
  const ConsultationPage({super.key});

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'AI კონსულტაცია',
          style: uiTextStyles.bodyBold16.copyWith(color: uiColors.primaryTextColor),
        ),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.psychology, size: 64, color: uiColors.accentColor.withValues(alpha: 0.4)),
            const SizedBox(height: 20),
            Text(
              'AI კონსულტაცია',
              style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor),
            ),
            const SizedBox(height: 8),
            Text(
              'დაუსვით იურიდიული კითხვა',
              style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
            ),
          ],
        ),
      ),
    );
  }
}
