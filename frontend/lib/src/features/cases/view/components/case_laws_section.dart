import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:ui_kit/ui_kit.dart';

/// Laws section displaying all referenced articles with their snippets and direct URLs.
class CaseLawsSection extends StatelessWidget {
  const CaseLawsSection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  Widget build(BuildContext context) {
    final uiColors = context.uiColors;
    final uiTextStyles = context.uiTextStyles;

    if (caseData.linkedArticles.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.gavel, size: 48, color: uiColors.accentColor.withValues(alpha: 0.5)),
            const SizedBox(height: 16),
            Text('კანონები ჯერ არ არის დაკავშირებული', style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor)),
          ],
        ),
      );
    }

    return ListView.separated(
      padding: const EdgeInsets.all(16),
      itemCount: caseData.linkedArticles.length,
      separatorBuilder: (_, __) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final article = caseData.linkedArticles[index];
        return Container(
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: uiColors.backgroundSecondaryColor,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: uiColors.accentColor.withValues(alpha: 0.1)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.menu_book, size: 16, color: uiColors.accentColor),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      article.title,
                      style: uiTextStyles.bodyBold14.copyWith(color: uiColors.primaryTextColor),
                    ),
                  ),
                ],
              ),
              if (article.snippet.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  article.snippet,
                  style: uiTextStyles.body14.copyWith(color: uiColors.secondaryTextColor),
                ),
              ],
              if (article.url != null && article.url!.isNotEmpty) ...[
                const SizedBox(height: 12),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton.icon(
                    onPressed: () => _launchUrl(article.url!),
                    icon: const Icon(Icons.open_in_new, size: 16),
                    label: const Text('სრულად ნახვა'),
                    style: TextButton.styleFrom(
                      foregroundColor: uiColors.accentColor,
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      backgroundColor: uiColors.accentColor.withValues(alpha: 0.1),
                    ),
                  ),
                ),
              ],
            ],
          ),
        );
      },
    );
  }

  Future<void> _launchUrl(String urlString) async {
    final uri = Uri.parse(urlString);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }
}
