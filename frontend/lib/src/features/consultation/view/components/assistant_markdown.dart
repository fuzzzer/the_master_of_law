import 'package:flutter/material.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:url_launcher/url_launcher.dart';

/// An assistant's answer, rendered.
///
/// The model writes markdown — bold, bullets, links to matsne.gov.ge — and a
/// plain text widget showed it verbatim: `* **სათაური:**` and raw
/// `[text](url)`. Every style here is a role from the pack; the sheet is
/// built from the theme and only its body and link roles are overridden.
class AssistantMarkdown extends StatelessWidget {
  const AssistantMarkdown(this.text, {super.key});

  final String text;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final body = type.body.copyWith(color: colors.ink);

    return MarkdownBody(
      data: text,
      selectable: true,
      styleSheet: MarkdownStyleSheet.fromTheme(Theme.of(context)).copyWith(
        p: body,
        listBullet: body,
        strong: body.copyWith(fontWeight: FontWeight.w600),
        a: body.copyWith(decoration: TextDecoration.underline),
        h1: type.titleM.copyWith(color: colors.ink),
        h2: type.titleS.copyWith(color: colors.ink),
        h3: type.titleS.copyWith(color: colors.ink),
      ),
      onTapLink: (_, href, __) async {
        if (href == null) return;
        final uri = Uri.tryParse(href);
        if (uri != null && await canLaunchUrl(uri)) await launchUrl(uri);
      },
    );
  }
}
