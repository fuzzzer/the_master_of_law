import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';
// `AppChipParent` — the shared parent-aware surface rule (M17 / T-0261).
import 'package:themasteroflaw/src/src.dart';

/// A tappable inline legal citation, with a **Georgian-safe** label.
///
/// The kit ships `FuzzzyCitationChip` and it does **not** fit here, for two
/// independent reasons — both filed as `PHASE_M_KIT_QUEUE` item 12:
///
/// 1. It renders `label.toUpperCase()` in `fuzzzyTextStyles.label`, the mono
///    **Latin-only** eyebrow role. Every citation label in this app is a
///    Georgian article title. (Same defect as item 11's `FuzzzyStatusChip`.)
/// 2. **It has no `onTap`.** All four of MoL's citation chips are navigation
///    affordances — three open an external URL, one routes to the article page.
///    Swapping to the kit widget would *lose an affordance*, which the Phase-M
///    change-vs-defect rubric (plan §4) classes as a defect, not a change.
///
/// So this is the kit's recipe rebuilt on the roles with a Georgian-capable
/// type role and a tap target — `RECIPE_NEW_WIDGET.md`'s success path, not a
/// gap. It keeps the kit's `law.cite.<qaId>` identifier so a saved QA script
/// survives the eventual swap.
///
/// Roles consumed: `surface`/`ground` per [parent] · 1px `line` border ·
///   `radius.s` (a small painted shape) · `density.chip` internal padding ·
///   `space.xs` icon↔label · `type.bodyS` in `ink`, underlined when tappable.
/// States: rest · press (an ink step — a boxed tappable with no ripple, the
///   one sanctioned variant for a chip this small) · disabled is not modelled
///   because a citation is either present and tappable or absent. Geometry is
///   constant: the underline is a text decoration, not a border, so it never
///   reflows.
/// QA: `law.cite.<qaId>` identifier + Key.
class AppCitationChip extends StatelessWidget {
  const AppCitationChip({
    super.key,
    required this.label,
    required this.parent,
    this.leading,
    this.trailing,
    this.onTap,
    this.maxLines = 1,
    this.qaId,
  });

  /// The article title, Georgian, rendered exactly as given — never uppercased.
  final String label;

  final AppChipParent parent;

  /// Usually `Icons.gavel` (a linked law) or `Icons.article_outlined`
  /// (a cited article). Takes the chip's own `ink` role via [IconTheme].
  final Widget? leading;

  /// Usually `Icons.open_in_new` when [onTap] leaves the app. Takes `inkMute`.
  final Widget? trailing;

  /// Tapping navigates. When null the chip is a plain marker: no underline, no
  /// hit target, no press feedback — the affordance and its signal appear and
  /// disappear together, which is the invariant the four hand-rolled copies
  /// each restated with a local `hasUrl` flag.
  final VoidCallback? onTap;

  final int maxLines;

  final String? qaId;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    // The parent-aware rule, in one place instead of four.
    final box = switch (parent) {
      AppChipParent.ground => colors.surface,
      AppChipParent.surface => colors.ground,
    };
    final tappable = onTap != null;

    final content = Container(
      padding: density.chip,
      decoration: BoxDecoration(
        color: box,
        borderRadius: BorderRadius.circular(radius.s),
        border: Border.all(color: colors.line),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (leading != null) ...[
            IconTheme.merge(
              data: IconThemeData(color: colors.ink, size: 12),
              child: leading!,
            ),
            SizedBox(width: space.xs),
          ],
          Flexible(
            child: Text(
              label,
              style: type.bodyS.copyWith(
                color: colors.ink,
                // The tappability's whole signal, now that the fork's
                // #1565C0 "link blue" is gone — blue is not a role in this
                // house. Without `decorationColor` the rule draws in the
                // INHERITED colour, which after the role swap is not always
                // the text's (M8 judgement 1).
                decoration: tappable ? TextDecoration.underline : null,
                decorationColor: tappable ? colors.ink : null,
              ),
              maxLines: maxLines,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          if (trailing != null) ...[
            SizedBox(width: space.xs),
            IconTheme.merge(
              data: IconThemeData(color: colors.inkMute, size: 12),
              child: trailing!,
            ),
          ],
        ],
      ),
    );

    return Semantics(
      // The kit widget's own string, deliberately — see the class doc.
      identifier: qaId == null ? null : 'law.cite.$qaId',
      // Own node, or the identifier merges into the enclosing bubble/card and
      // becomes unreachable to QA (RECIPE_NEW_WIDGET §5.1).
      container: true,
      button: tappable,
      label: label,
      child: KeyedSubtree(
        key: qaId == null ? null : Key('law.cite.$qaId'),
        child: tappable
            // The kit's tap primitive. InkWell/InkResponse are banned (§5.3),
            // so there is no ripple to fall back on.
            ? GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTap: onTap,
                child: content,
              )
            : content,
      ),
    );
  }
}
