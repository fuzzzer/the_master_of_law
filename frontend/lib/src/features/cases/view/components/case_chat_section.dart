import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/src.dart';

/// In-case AI chat section. Placeholder until API integration (Step 4).
/// Shows context banner and CTA to start consultation.
class CaseChatSection extends StatelessWidget {
  const CaseChatSection({super.key, required this.caseId});
  final String caseId;

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    return Padding(
      padding: const EdgeInsets.all(20),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          // Context banner
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
            decoration: BoxDecoration(
              color: uiColors.backgroundSecondaryColor,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.folder_open, size: 16, color: uiColors.accentColor),
                const SizedBox(width: 8),
                Text(
                  'AI-ს აქვს საქმის სრული კონტექსტი',
                  style: uiTextStyles.labelBold12.copyWith(color: uiColors.secondaryTextColor),
                ),
              ],
            ),
          ),
          const Spacer(),
          Icon(Icons.psychology, size: 64, color: uiColors.accentColor.withValues(alpha: 0.4)),
          const SizedBox(height: 20),
          Text(
            'AI კონსულტაცია',
            style: uiTextStyles.headlineBold20.copyWith(color: uiColors.primaryTextColor),
          ),
          const SizedBox(height: 8),
          Text(
            'დაუსვით AI-ს ნებისმიერი იურიდიული კითხვა.\nპასუხი მოიცავს ზუსტ კანონის მითითებებს.',
            style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 24),
          // Chat input placeholder
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
            decoration: BoxDecoration(
              color: uiColors.backgroundSecondaryColor,
              borderRadius: BorderRadius.circular(24),
              border: Border.all(color: uiColors.secondaryTextColor.withValues(alpha: 0.15)),
            ),
            child: Row(
              children: [
                IconButton(
                  icon: Icon(Icons.attach_file, color: uiColors.secondaryTextColor, size: 22),
                  onPressed: () {},
                ),
                Expanded(
                  child: TextField(
                    style: uiTextStyles.body14.copyWith(color: uiColors.primaryTextColor),
                    decoration: InputDecoration(
                      hintText: 'აღწერეთ ახალი გარემოება...',
                      hintStyle: uiTextStyles.body14.copyWith(
                        color: uiColors.secondaryTextColor.withValues(alpha: 0.5),
                      ),
                      border: InputBorder.none,
                      contentPadding: EdgeInsets.zero,
                    ),
                  ),
                ),
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    color: uiColors.accentColor,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(Icons.arrow_upward, color: uiColors.backgroundPrimaryColor, size: 20),
                ),
              ],
            ),
          ),
          const Spacer(),
        ],
      ),
    );
  }
}
