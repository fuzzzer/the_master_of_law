import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

/// A surface card with a `line` hairline and a coloured accent rule down its
/// left edge — `FuzzzyCard(leadingRule:)`'s shape, app-side.
///
/// **Why this file exists (T-0254).** Four call sites re-derived the kit's
/// accent-card idiom from its *description* as a non-uniform `Border` plus a
/// `borderRadius`:
///
/// ```dart
/// border: Border(
///   left: BorderSide(color: accent, width: 4),
///   top: BorderSide(color: colors.line), // …right, bottom
/// ),
/// borderRadius: BorderRadius.circular(radius.l),
/// ```
///
/// Flutter paints a non-uniform border with a radius **only when
/// `_distinctVisibleColors()` yields exactly one colour**
/// (`box_border.dart:726-746`, SDK 3.32.0); two visible colours throw
/// `A borderRadius can only be given on borders with uniform colors` from
/// `paint()`, on the first frame, with no interaction. Every static gate
/// (`analyze` 0/0/2, `flutter test`, the consumer guard, `build bundle`) was
/// green while the cases list was throwing on every build.
///
/// The kit is **not** at fault — `containers/fuzzzy_card.dart:51-108` does it
/// correctly, and this widget copies that: a **uniform** `Border.all(line)` box
/// inside a `ClipRRect`, with the rule as a `Positioned` overlay clipped to the
/// same radius so it follows the rounded corners.
///
/// **Why it is not simply `FuzzzyCard`.** `FuzzzyCard` hardcodes `radius.l` and
/// a 4px rule; the four sites need `radius.l`/`radius.m` and 4px/3px, and two of
/// them sit inside a `Dismissible` with their own `GestureDetector`. Adopting it
/// unchanged would have silently changed corner radii — an unasked-for visual
/// change on the eve of the M14 matrix. This widget keeps the geometry the
/// migration already chose and fixes only the paint bug. It is deliberately
/// presentation-only: tap handling stays at the call site, exactly where it was.
///
/// Roles consumed: `surface` fill · 1px `line` border · caller-supplied radius
///   role · caller-supplied rule role · caller-supplied density padding.
/// States: rest only — this is a painted surface, not a control.
/// QA: emits the kit's own `card.<qaId>` identifier + `Key` when [qaId] is set,
///   so that when this collapses into `FuzzzyCard(leadingRule:)` saved QA
///   scripts keep working.
class AppRuleCard extends StatelessWidget {
  const AppRuleCard({
    super.key,
    required this.child,
    required this.rule,
    required this.borderRadius,
    required this.padding,
    this.ruleWidth = 4,
    this.qaId,
  });

  final Widget child;

  /// The accent rule's role colour. Pass `colors.line` for "no accent" — the
  /// rule then simply repaints the hairline, which is what the resolved state
  /// of a clarification tile wants.
  final Color rule;

  /// The corner radius role (`radius.l` / `radius.m`). Required rather than
  /// defaulted: the four call sites genuinely disagree, and a default here
  /// would silently restyle whichever one forgot to pass it.
  final double borderRadius;

  /// The internal inset — a density role (`density.card` / `.panel` / `.tile`).
  final EdgeInsetsGeometry padding;

  /// The rule's thickness. 4px everywhere except the clarification tile, whose
  /// 3px matches `FuzzzyBanner`'s shape.
  final double ruleWidth;

  final String? qaId;

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;

    final box = Container(
      padding: padding,
      decoration: BoxDecoration(
        color: colors.surface,
        // 🔴 UNIFORM — the whole point of this widget. Never reintroduce a
        // per-side `Border(...)` here while a `borderRadius` is present.
        border: Border.all(color: colors.line),
        borderRadius: BorderRadius.circular(borderRadius),
      ),
      child: child,
    );

    final decorated = ClipRRect(
      borderRadius: BorderRadius.circular(borderRadius),
      child: Stack(
        children: [
          box,
          Positioned(
            left: 0,
            top: 0,
            bottom: 0,
            // Purely presentational — never intercept a tap meant for the
            // card's own gesture detector.
            child: IgnorePointer(
              child: Container(width: ruleWidth, color: rule),
            ),
          ),
        ],
      ),
    );

    if (qaId == null) return decorated;
    return Semantics(
      identifier: 'card.$qaId',
      // Own node: without it this fragment merges into an enclosing container
      // and the identifier becomes unreachable (kit GUIDELINES §9.4).
      container: true,
      child: KeyedSubtree(key: Key('card.$qaId'), child: decorated),
    );
  }
}
