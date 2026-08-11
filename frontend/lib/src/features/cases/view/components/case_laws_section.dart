import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:themasteroflaw/src/src.dart';
import 'package:url_launcher/url_launcher.dart';

/// Laws section displaying all referenced articles with their snippets and direct URLs.
class CaseLawsSection extends StatelessWidget {
  const CaseLawsSection({super.key, required this.caseData});
  final CaseData caseData;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    if (caseData.linkedArticles.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            // Dimension: the oversized empty-state glyph, on M4's `inkFaint`.
            Icon(Icons.gavel, size: 48, color: colors.inkFaint),
            SizedBox(height: space.l),
            Text(
              'კანონები ჯერ არ არის დაკავშირებული',
              style: type.body.copyWith(color: colors.inkMute),
            ),
          ],
        ),
      );
    }

    return ListView.separated(
      padding: density.screen,
      itemCount: caseData.linkedArticles.length,
      separatorBuilder: (_, __) => SizedBox(height: space.m),
      itemBuilder: (context, index) {
        final article = caseData.linkedArticles[index];
        return Container(
          padding: density.card,
          decoration: BoxDecoration(
            color: colors.surface,
            borderRadius: BorderRadius.circular(radius.m),
            // The fork's gold border at alpha 0.1 is the "tinted border" row
            // MAPPING §2.2 sends to a line role — and at 0.1 it was barely a
            // border at all. It is now the `line` hairline every card in this
            // app carries.
            border: Border.all(color: colors.line),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  // An inline leading glyph takes the SAME rung as the text it
                  // leads (M9 §E); this one leads the card's `ink` title.
                  Icon(Icons.menu_book, size: 16, color: colors.ink),
                  SizedBox(width: space.s),
                  Expanded(
                    child: Text(
                      article.title,
                      style: type.titleS.copyWith(color: colors.ink),
                    ),
                  ),
                ],
              ),
              if (article.snippet.isNotEmpty) ...[
                SizedBox(height: space.s),
                Text(
                  article.snippet,
                  style: type.body.copyWith(color: colors.inkMute),
                ),
              ],
              if (article.url != null && article.url!.isNotEmpty) ...[
                SizedBox(height: space.m),
                Align(
                  alignment: Alignment.centerRight,
                  child: TextButton.icon(
                    onPressed: () => _launchUrl(article.url!),
                    icon: const Icon(Icons.open_in_new, size: 16),
                    label: const Text('სრულად ნახვა'),
                    // The fork gave this a gold FILL at alpha 0.1 plus a gold
                    // label — a tinted panel behind a text button, which is
                    // two hierarchy claims for one secondary action. It is now
                    // `FuzzzyButton.secondary`'s shape: an `ink` label inside
                    // a `lineStrong` outline, no fill (M8 judgement 9).
                    style: TextButton.styleFrom(
                      foregroundColor: colors.ink,
                      side: BorderSide(color: colors.lineStrong),
                      padding: density.chip,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(radius.m),
                      ),
                      textStyle: type.control,
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
