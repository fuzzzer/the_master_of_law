import 'package:flutter/material.dart';
import 'package:fuzzzy_law/src/src.dart';

/// The eight legal-domain colours — **the one sanctioned literal palette in
/// this app**, and the only place `Color(0x…)` is correct in `lib/`.
///
/// Phase M · Unit A, checkpoint M7.
///
/// **Why these are not kit roles.** `fuzzzy_ui_kit` deliberately does not own
/// a legal taxonomy: `design/harvest/mol.md` §3 and the owner's ruling put the
/// eight-colour palette app-side and keep the kit's chip mechanism neutral
/// (`FuzzzyFilterChip.dotColor` / `FuzzzyCard.leadingRule` take a caller-supplied
/// colour). Remapping them onto `success`/`warning`/`info`/… would be wrong
/// twice over: it would invent semantics the taxonomy does not have (there is
/// nothing "successful" about civil law), and it would spend the semantic roles
/// on decoration. `MAPPING.md` §2.1 marks this row **locked**.
///
/// **Where a domain colour may appear.** Only as a **rule or a dot** — the 4px
/// left rule on a case card and the 8px leading disc on a chip. Never as text,
/// never as a panel fill, never as a border. That is the kit's neutral
/// mechanism, and it keeps every screen monochrome apart from one small
/// identifying mark.
///
/// The values were lifted verbatim at M7 from the fork's
/// `packages/ui_kit/lib/src/colors/ui_kit_colors.dart` (`*ColorDark` → [dark],
/// the plain names → [light]). **That file no longer exists** — M12 deleted
/// `packages/ui_kit` — so this class is now the only surviving copy of the
/// taxonomy and the hexes here cannot be re-derived from anything in the repo.
/// Registered as a [ThemeExtension] rather than a static map so it follows the
/// skin, exactly as the fork's two palettes did.
@immutable
class LegalDomainColors extends ThemeExtension<LegalDomainColors> {
  const LegalDomainColors({
    required this.criminal,
    required this.civil,
    required this.administrative,
    required this.labor,
    required this.tax,
    required this.family,
    required this.property,
    required this.other,
  });

  final Color criminal;
  final Color civil;
  final Color administrative;
  final Color labor;
  final Color tax;
  final Color family;
  final Color property;
  final Color other;

  /// Night-skin taxonomy (the fork's `*ColorDark`).
  static const LegalDomainColors dark = LegalDomainColors(
    criminal: Color(0xFFE5534B),
    civil: Color(0xFF5B9BD5),
    administrative: Color(0xFF4CAF79),
    labor: Color(0xFFE8A838),
    tax: Color(0xFF9B72CF),
    family: Color(0xFFE88BA8),
    property: Color(0xFF4DB6AC),
    other: Color(0xFF8B95A5),
  );

  /// Paper-skin taxonomy (the fork's light values).
  static const LegalDomainColors light = LegalDomainColors(
    criminal: Color(0xFFD32F2F),
    civil: Color(0xFF3A7BBF),
    administrative: Color(0xFF2E7D50),
    labor: Color(0xFFC68A1D),
    tax: Color(0xFF7B4FB0),
    family: Color(0xFFD06B8A),
    property: Color(0xFF339688),
    other: Color(0xFF6B7280),
  );

  /// The single domain→colour switch for the whole app.
  ///
  /// Replaces three byte-identical private `_domainColor` helpers that used to
  /// live in `case_card.dart`, `new_case_sheet.dart` and
  /// `case_workspace_page.dart` (`MAPPING.md` §2.1).
  Color of(LegalDomain domain) => switch (domain) {
    LegalDomain.criminal => criminal,
    LegalDomain.civil => civil,
    LegalDomain.administrative => administrative,
    LegalDomain.labor => labor,
    LegalDomain.tax => tax,
    LegalDomain.family => family,
    LegalDomain.property => property,
    LegalDomain.other => other,
  };

  @override
  LegalDomainColors copyWith({
    Color? criminal,
    Color? civil,
    Color? administrative,
    Color? labor,
    Color? tax,
    Color? family,
    Color? property,
    Color? other,
  }) => LegalDomainColors(
    criminal: criminal ?? this.criminal,
    civil: civil ?? this.civil,
    administrative: administrative ?? this.administrative,
    labor: labor ?? this.labor,
    tax: tax ?? this.tax,
    family: family ?? this.family,
    property: property ?? this.property,
    other: other ?? this.other,
  );

  @override
  LegalDomainColors lerp(ThemeExtension<LegalDomainColors>? other, double t) {
    if (other is! LegalDomainColors) return this;
    return LegalDomainColors(
      criminal: Color.lerp(criminal, other.criminal, t)!,
      civil: Color.lerp(civil, other.civil, t)!,
      administrative: Color.lerp(administrative, other.administrative, t)!,
      labor: Color.lerp(labor, other.labor, t)!,
      tax: Color.lerp(tax, other.tax, t)!,
      family: Color.lerp(family, other.family, t)!,
      property: Color.lerp(property, other.property, t)!,
      other: Color.lerp(this.other, other.other, t)!,
    );
  }
}

/// `context.legalDomainColors` — same shape as the kit's `context.fuzzzy*`
/// accessors, so a call site reads the taxonomy the same way it reads a role.
extension LegalDomainColorsContext on BuildContext {
  LegalDomainColors get legalDomainColors =>
      Theme.of(this).extension<LegalDomainColors>()!;
}
