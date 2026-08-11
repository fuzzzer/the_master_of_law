import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_ui_kit/fuzzzy_ui_kit_guard.dart';

/// The kit consumer guard, as a **committed** check.
///
/// Phase M · Unit A · M13 (S7). Copied from `design/GUARD_TEMPLATE.md` §2 with
/// three deliberate deviations, each explained below. Until this file existed,
/// the guard was a command someone had to remember to type — `M0…M12` ran it by
/// hand at every close, which is exactly the kind of discipline that survives
/// twelve checkpoints and then quietly stops. `fvm flutter test` now fails if
/// the app grows a blocking design literal.
///
/// **It is still a floor, not a certificate** (`USING.md` §10): it cannot see
/// whether a value is on the right axis, whether the role chosen makes sense,
/// or whether a screen survives a `stressPack` swap. Overflow is a *runtime*
/// property and belongs to M14.
///
/// ---
///
/// **Deviation 1 — the allow-list is read from `.fuzzzy_guard_allow`, not
/// restated as a `const _allow` set.** The template inlines the pins in Dart.
/// This app already had the file, because `bin/guard.dart`'s `--allow=` takes
/// one, and the run's own gate is documented as
/// `fvm dart run fuzzzy_ui_kit:guard lib --allow=.fuzzzy_guard_allow`. Two
/// copies of a line-exact pin list would drift the first time either was
/// edited, and the drift would be silent in the direction that matters (a pin
/// present here but not there = a violation this test hides from the CLI). The
/// parser below is byte-for-byte the CLI's, so both read the same set.
///
/// **Deviation 2 — rotted pins fail.** See [_rottedPins]. This is the M12 trap,
/// mechanised.
///
/// **Deviation 3 — the advisory budget is 24, not the template's 0.** See
/// [_advisoryBudget].
void main() {
  test('no design literal escapes the brand pack', () {
    final violations = fuzzzyGuardScan(directory: 'lib', allow: _allow());

    expect(
      fuzzzyGuardBlocking(violations),
      isEmpty,
      reason: fuzzzyGuardReport(violations),
    );

    // Advisory hits cannot fail a build — `literal-gap` fires on the certified
    // 44px touch target as readily as on an unlooked-up gap — but they must not
    // grow unwatched. Pinning the count makes a new one a decision.
    expect(
      fuzzzyGuardAdvisory(violations).length,
      lessThanOrEqualTo(_advisoryBudget),
      reason: fuzzzyGuardReport(violations),
    );
  });

  // ── Deviation 2 ────────────────────────────────────────────────────────────
  //
  // 🔴 THE M12 TRAP, MECHANISED. Pins are line-exact, and a pin that stops
  // matching does not warn — it is simply skipped, the violation it used to
  // cover comes back as a fresh blocking hit somewhere else in the report, and
  // the "N pinned" counter still prints N. At M12 a TWO-LINE DOC-COMMENT edit
  // at the top of `legal_domain_colors.dart` pushed all 16 taxonomy literals
  // down by two lines; 12 pins still matched by coincidence (the ranges
  // overlapped) and 4 silently did not.
  //
  // A pin that matches nothing is either stale or a typo. Neither is ever
  // correct, and both are invisible in the CLI's output. This is the assertion
  // the template does not have and this app needed.
  test('every pin in .fuzzzy_guard_allow still matches a real violation', () {
    final rotted = _rottedPins();

    expect(
      rotted,
      isEmpty,
      reason:
          'These pins in .fuzzzy_guard_allow match no violation. A pinned line '
          'moved (a comment edit is enough) or the pin was mistyped, so the '
          'site it was written for is no longer covered:\n'
          '  ${rotted.join('\n  ')}\n'
          'Re-run `fvm dart run fuzzzy_ui_kit:guard lib` with NO --allow, find '
          'each site by what it paints, and re-pin it at its new line. Do not '
          'delete the pin to make this pass.',
    );
  });
}

/// The one allow-list, parsed exactly as `bin/guard.dart` parses it: one
/// `path:line` pin per line, `#` comments and blanks dropped. Paths are
/// relative to the **scanned root**, so they start `src/…` for `guard lib`.
Set<String> _allow() {
  final file = File(_allowPath);
  if (!file.existsSync()) {
    fail(
      '$_allowPath is missing. It is part of the gate, not a convenience: '
      "MoL's owner-locked LegalDomainColors taxonomy is 16 sanctioned "
      'literals, so `guard lib` can never be green without it.',
    );
  }
  return file
      .readAsLinesSync()
      .map((l) => l.split('#').first.trim())
      .where((l) => l.isNotEmpty)
      .toSet();
}

/// Pins that no longer name a real violation site.
///
/// Scanned with an EMPTY allow-list so every site is reported, then every pin
/// is checked against the set of real `path:line` keys.
List<String> _rottedPins() {
  final all = fuzzzyGuardScan(directory: 'lib').map((v) => v.pin).toSet();
  return (_allow().difference(all).toList())..sort();
}

const _allowPath = '.fuzzzy_guard_allow';

/// **24, and deliberately not 0.**
///
/// `GUARD_TEMPLATE.md` §2 says to set this to the count on the day you migrate
/// and then drive it down. Every one of today's 24 was read and sorted by hand
/// at M13, and the sort is the honest part of this number:
///
/// - **13 are reviewed dimensions**, each carrying a one-line `// Dimension:`
///   justification written at the checkpoint that created it — the in-button
///   and in-flow spinner footprints (24/16/20/18px), the strength ring's 64px
///   box, the timeline rail's 32px gutter, the reserved 80px back-button slot,
///   the law sheet's 200px loading reservation, the 48px full-width CTA, and
///   the 7px typing dot's 2.5px optical half-gap. `literal-gap` cannot tell any
///   of these from a gap, which is exactly why the rule is advisory.
/// - **1 is a pure false positive.** `case_chat_section.dart:203` is
///   `EdgeInsets.fromLTRB(space.l, space.m, space.l, 0)` — fully role-driven;
///   the scanner matched the literal `0`.
/// - **10 are `lib/src/core/services/dev_panel/` geometry that has NOT been
///   swapped onto roles** — 8 `EdgeInsets` + 2 `SizedBox` across
///   `dev_panel_screen` (46, 213, 219), `logs_screen` (35, 99, 108),
///   `work_in_progress_features_display_screen` (15) and `dev_panel_tile`
///   (32, 37, 38). M10b took that feature's *colour* and *type* onto roles and
///   left its *geometry*. They are real, they are honest, and they are
///   **deliberately not pinned** — pinning them is precisely the "bulk-pin for
///   a green tick" the template warns about, and most are ordinary gutters
///   (16/32/12) that map straight onto `space.{l,xxl,m}`.
///
/// So: do not lower this by pinning. Lower it by putting the dev-panel geometry
/// on roles, which should land the budget at **14**.
const _advisoryBudget = 24;
