import 'package:flutter/material.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit.dart';

/// The voice of an [AppStatusChip] — chooses the dot, border and label role.
///
/// Deliberately mirrors the kit's own `FuzzzyStatusKind` names so that the day
/// `PHASE_M_KIT_QUEUE` item 11 lands, this file is deleted and every call site
/// swaps to `FuzzzyStatusChip(kind: FuzzzyStatusKind.<same name>)` with no
/// rename. `live` is intentionally absent: it pulses, and nothing in MoL's
/// status taxonomy is a live/streaming state.
enum AppStatusKind { success, info, warning, error, neutral }

/// A compact status chip with a leading dot and a **Georgian-safe** label.
///
/// This is `FuzzzyStatusChip`'s recipe, app-side, and it exists for exactly one
/// reason: the kit widget hardcodes `fuzzzyTextStyles.label.toUpperCase()` —
/// the **mono, Latin-only** eyebrow role. Space Mono has no Georgian block, so
/// every label in this app would fall to a platform font at platform metrics,
/// and `toUpperCase()` is a no-op on a unicase script. Filed as
/// `PHASE_M_KIT_QUEUE` item 11 (additive, not blocking). **When that lands,
/// delete this file** — everything else here is copied from
/// `feedback/fuzzzy_status_chip.dart:75-98` exactly.
///
/// Roles consumed: no fill · 1px `Color.lerp(ground, role, 0.40)` border ·
///   `radius.s` (a small painted shape) · `density.chip` internal padding ·
///   `space.s` dot↔label (§4.2's canonical icon↔label gap) ·
///   `type.control` in the kind's role.
/// States: rest only — this is a non-interactive marker, so there is no
///   hover/press/focus/disabled to keep geometry constant across.
/// QA: `chip.<qaId>` identifier + Key, matching the kit widget's own string so
///   saved QA scripts survive the eventual swap.
class AppStatusChip extends StatelessWidget {
  const AppStatusChip({
    super.key,
    required this.label,
    required this.kind,
    this.dot = true,
    this.qaId,
  });

  /// The Georgian (or any non-Latin) label. Rendered as written — never
  /// uppercased, which is the whole point of this widget.
  final String label;

  final AppStatusKind kind;

  /// The 8px leading disc. Kept as a flag rather than a variant because it
  /// changes nothing about the chip's identity, only whether the role is shown
  /// twice.
  final bool dot;

  final String? qaId;

  Color _role(FuzzzyColors c) => switch (kind) {
    AppStatusKind.success => c.success,
    AppStatusKind.info => c.info,
    AppStatusKind.warning => c.warning,
    AppStatusKind.error => c.destructive,
    AppStatusKind.neutral => c.inkMute,
  };

  @override
  Widget build(BuildContext context) {
    final colors = context.fuzzzyColors;
    final type = context.fuzzzyTextStyles;
    final space = context.fuzzzySpace;
    final radius = context.fuzzzyRadius;
    final density = context.fuzzzyDensity;

    final role = _role(colors);
    // `neutral` draws a plain grey outline decoupled from its dot; every other
    // kind colour-mixes its own role into the border. Kit behaviour, copied.
    final border = kind == AppStatusKind.neutral
        ? Color.lerp(colors.ground, colors.lineStrong, 0.40)!
        : Color.lerp(colors.ground, role, 0.40)!;

    return Semantics(
      identifier: qaId == null ? null : 'chip.$qaId',
      // Own node: without this the fragment merges into the enclosing card and
      // the identifier is unreachable (RECIPE_NEW_WIDGET §5.1).
      container: true,
      label: label,
      child: KeyedSubtree(
        key: qaId == null ? null : Key('chip.$qaId'),
        child: Container(
          padding: density.chip,
          decoration: BoxDecoration(
            border: Border.all(color: border),
            borderRadius: BorderRadius.circular(radius.s),
          ),
          // 🔴 M14b. Under the STRESS pack the case-workspace header
          // (`case_workspace_page.dart:170`) overflowed by 39 px on the right
          // at every one of its ten tabs: two of these chips plus a `%`
          // readout, and a chip took its natural width no matter what the row
          // could spare. A chip that cannot give ground is a layout hazard
          // wherever two of them share a line.
          //
          // So the label becomes `Flexible` — **but only when this chip was
          // actually given a bounded width.** A `Flexible` inside a `Row` that
          // receives unbounded main-axis constraints THROWS, and a chip that
          // is a plain (non-flex) child of a `Row` receives exactly that. The
          // `LayoutBuilder` is what makes the widget safe at all five call
          // sites: constrain the chip at the call site and it ellipses;
          // leave it unconstrained and it behaves exactly as before.
          child: LayoutBuilder(
            builder: (context, constraints) {
              final labelText = Text(
                label,
                style: type.control.copyWith(color: role),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              );
              return Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (dot) ...[
                    Container(
                      // Dimension: §4.4's ONE sanctioned status-dot diameter.
                      // In this app it also replaces the fork's coloured emoji
                      // (🟢/🟡/⚪, ✓/◐/○) — the disc IS what those imitated.
                      width: 8,
                      height: 8,
                      decoration: BoxDecoration(
                        color: role,
                        borderRadius: BorderRadius.circular(radius.circle),
                      ),
                    ),
                    SizedBox(width: space.s),
                  ],
                  // `control` IS the w600 role — the fork's caption11 +
                  // `fontWeight: w600` override becomes a role choice, and the
                  // label is NOT uppercased (see the class doc).
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
