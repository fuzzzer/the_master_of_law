import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
import 'package:themasteroflaw/src/src.dart';

/// The legal-domain pill: an 8 px taxonomy disc and a Georgian short label in
/// a monochrome outlined box.
///
/// `FuzzzyFilterChip`'s neutral `dotColor` variant
/// (`inputs/fuzzzy_filter_chip.dart:105-130`) rebuilt app-side and
/// non-interactive, because the kit widget is a *filter* — it owns selection
/// state and a tap callback, and this pill is a read-only taxonomy marker at
/// both of its call sites. The taxonomy colour is the disc and **only** the
/// disc; the box and the label stay monochrome, which is the whole reason
/// `LegalDomainColors` survives the migration as an owner-locked palette
/// (`harvest/mol.md` §3) without becoming a second brand.
///
/// ## Why this file exists — `T-0261`
///
/// There were **two** private `_DomainChip` classes, same name, same shape,
/// one in `case_card.dart` and one in `case_workspace_page.dart`. S9's review
/// caught them diverging in three ways at once:
///
/// 1. Only the workspace copy carried M14b's `LayoutBuilder` + `Flexible`
///    ellipsis hardening. The `case_card` copy was a plain non-flex child of a
///    `Row`, and `RenderFlex` hands non-flex children `maxWidth: infinity`, so
///    a long label there would **overflow** rather than give ground.
/// 2. One took a `dotColor`, the other read `context.legalDomainColors`.
/// 3. **Neither emitted a QA identifier**, unlike [AppStatusChip] and
///    [AppCitationChip] — so both were invisible to Marionette scripts, which
///    is precisely why no matrix cell could ever have addressed them.
///
/// The same run collapsed five status chips into [AppStatusChip] and four
/// citation chips into [AppCitationChip] and then left this pair duplicated.
/// Consolidating it here also means `T-0263`'s header work is done **once**.
///
/// Roles consumed: `surface`/`ground` per [parent] · 1 px `line` border ·
///   `radius.s` · `density.chip` internal padding · `space.s` disc↔label ·
///   `type.control` in `inkMute` · `radius.circle` on the disc.
/// States: none — this pill is not interactive at either call site, which is
///   why it is not a `FuzzzyFilterChip` and why there is no tap target to
///   size. Geometry is constant.
/// QA: `chip.<qaId>` identifier + `Key`, the same string [AppStatusChip] and
///   the kit's own chips emit, so one saved script addresses all of them.
class AppDomainChip extends StatelessWidget {
  const AppDomainChip({
    super.key,
    required this.domain,
    required this.parent,
    this.qaId,
  });

  /// The taxonomy value. The chip resolves both its label
  /// ([LegalDomain.shortLabelKa]) and its disc colour from this — the two used
  /// to be supplied independently, which is how a caller could pass a disc
  /// colour that did not match the domain it labelled.
  final LegalDomain domain;

  /// See [AppChipParent]. There is no default: the rule is easy to get
  /// backwards and a wrong guess is invisible on one skin.
  final AppChipParent parent;

  /// Suffix for the `chip.<qaId>` Semantics identifier and `Key`.
  final String? qaId;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;

    final box = switch (parent) {
      AppChipParent.ground => colors.surface,
      AppChipParent.surface => colors.ground,
    };

    return Semantics(
      identifier: qaId == null ? null : 'chip.$qaId',
      // Own node, or the fragment merges into the enclosing card and the
      // identifier is unreachable (RECIPE_NEW_WIDGET §5.1).
      container: true,
      label: domain.shortLabelKa,
      child: KeyedSubtree(
        key: qaId == null ? null : Key('chip.$qaId'),
        child: Container(
          padding: context.fuzzzyDensity.chip,
          decoration: BoxDecoration(
            color: box,
            border: Border.all(color: colors.line),
            borderRadius: BorderRadius.circular(radius.s),
          ),
          // The M14b guard, now at both call sites rather than one: the label
          // becomes `Flexible` **only when this chip was given a bounded
          // width**. A `Flexible` under unbounded main-axis constraints throws,
          // and a plain (non-flex) child of a `Row` receives exactly that — so
          // constrain the chip at the call site and it ellipses, leave it
          // unconstrained and it takes its natural width as before.
          child: LayoutBuilder(
            builder: (context, constraints) {
              final labelText = Text(
                domain.shortLabelKa,
                style: type.control.copyWith(color: colors.inkMute),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              );
              return Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Container(
                    // Dimension: §4.4's one sanctioned status-dot diameter.
                    // It replaces the fork's '⚖️ ' emoji prefix (which also
                    // carried a hardcoded `fontSize: 12`) — the disc is what
                    // that emoji stood in for, and unlike it, it actually
                    // names the domain.
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      color: context.legalDomainColors.of(domain),
                      borderRadius: BorderRadius.circular(radius.circle),
                    ),
                  ),
                  SizedBox(width: space.s),
                  if (constraints.maxWidth.isFinite)
                    Flexible(child: labelText)
                  else
                    labelText,
                ],
              );
            },
          ),
        ),
      ),
    );
  }
}
