import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

import 'legal_documents_data.dart';

/// Renders one [LegalDocument] — the privacy policy or the terms.
///
/// One page class for both, because a legal text is a title, a date and a list
/// of headed sections, and two near-identical page widgets would drift the
/// first time either was edited.
///
/// Every dimension and colour here is a role from the kit. Nothing is a
/// literal, so the page follows a brand-pack swap and `fuzzzy_guard_test`
/// stays quiet.
class LegalDocumentPage extends StatelessWidget {
  const LegalDocumentPage({required this.document, super.key});

  final LegalDocument document;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final density = context.fuzzzyDensity;

    return Scaffold(
      appBar: AppBar(title: Text(document.title)),
      // Scrollable, not a Column: these texts are long, they are read at the
      // reader's own font scale, and a legal notice that cannot be scrolled to
      // the end is a legal notice that was not given.
      body: ListView(
        padding: density.screen,
        children: [
          Text(
            'ბოლო განახლება: ${document.updated}',
            style: type.bodyS.copyWith(color: colors.inkMute),
          ),
          SizedBox(height: space.m),
          Text(document.intro, style: type.body.copyWith(color: colors.ink)),
          SizedBox(height: space.xl),
          for (final section in document.sections) ...[
            Text(
              section.heading,
              style: type.titleS.copyWith(color: colors.ink),
            ),
            SizedBox(height: space.s),
            for (final paragraph in section.paragraphs) ...[
              Text(paragraph, style: type.body.copyWith(color: colors.ink)),
              SizedBox(height: space.m),
            ],
            SizedBox(height: space.l),
          ],
        ],
      ),
    );
  }
}

/// The privacy policy, at `/profile/privacy`.
class PrivacyPolicyPage extends StatelessWidget {
  const PrivacyPolicyPage({super.key});

  @override
  Widget build(BuildContext context) =>
      const LegalDocumentPage(document: privacyPolicy);
}

/// The terms of service, at `/profile/terms`.
class TermsOfServicePage extends StatelessWidget {
  const TermsOfServicePage({super.key});

  @override
  Widget build(BuildContext context) =>
      const LegalDocumentPage(document: termsOfService);
}
