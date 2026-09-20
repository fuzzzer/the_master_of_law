/// All legal domain categories used across the app.
enum LegalDomain {
  criminal,
  civil,
  administrative,
  labor,
  tax,
  family,
  property,
  other;

  /// Georgian display name.
  String get displayNameKa => switch (this) {
    criminal => 'სისხლის სამართალი',
    civil => 'სამოქალაქო',
    administrative => 'ადმინისტრაციული',
    labor => 'შრომის',
    tax => 'საგადასახადო',
    family => 'ოჯახის',
    property => 'საკუთრების',
    other => 'სხვა',
  };

  /// English display name.
  String get displayNameEn => switch (this) {
    criminal => 'Criminal',
    civil => 'Civil',
    administrative => 'Administrative',
    labor => 'Labor',
    tax => 'Tax',
    family => 'Family',
    property => 'Property',
    other => 'Other',
  };

  /// Short Georgian label for chips.
  String get shortLabelKa => switch (this) {
    criminal => 'სისხ.',
    civil => 'სამოქ.',
    administrative => 'ადმინ.',
    labor => 'შრომ.',
    tax => 'საგად.',
    family => 'ოჯახ.',
    property => 'საკუთრ.',
    other => 'სხვა',
  };
}

/// Case lifecycle status.
enum CaseStatus {
  active,
  pending,
  closed;

  String get displayNameKa => switch (this) {
    active => 'აქტიური',
    pending => 'მომლოდინე',
    closed => 'დახურული',
  };

  String get displayNameEn => switch (this) {
    active => 'Active',
    pending => 'Pending',
    closed => 'Closed',
  };
}

/// Fact classification for categorization.
enum FactClassification {
  favorable,
  unfavorable,
  neutral;

  String get displayNameKa => switch (this) {
    favorable => 'ხელსაყრელი',
    unfavorable => 'არახელსაყრელი',
    neutral => 'ნეიტრალური',
  };

  /// Glyph for the PLAIN-TEXT clipboard export only (`CaseExportHelper`),
  /// never for UI. Renamed from `emoji` at M11b: the UI's classification
  /// signal is a role-coloured 4px rule + 8px dot (M8), and a member called
  /// `emoji` was an open invitation to wire a picture back into a screen.
  /// A text document cannot render an `IconData`, so this one stays a glyph.
  String get exportGlyph => switch (this) {
    favorable => '✅',
    unfavorable => '❌',
    neutral => 'ℹ️',
  };
}

/// Argument strength rating.
enum ArgumentStrength {
  strong,
  moderate,
  weak;

  String get displayNameKa => switch (this) {
    strong => 'ძლიერი',
    moderate => 'საშუალო',
    weak => 'სუსტი',
  };
}

/// Evidence type classification.
enum EvidenceType {
  document,
  photo,
  screenshot,
  receipt,
  other;

  String get displayNameKa => switch (this) {
    document => 'დოკუმენტი',
    photo => 'ფოტო',
    screenshot => 'სქრინშოტი',
    receipt => 'ქვითარი',
    other => 'სხვა',
  };
}

/// Timeline event type.
enum TimelineEventType {
  past,
  deadline,
  milestone;

  String get displayNameKa => switch (this) {
    past => 'წარსული',
    deadline => 'ვადა',
    milestone => 'ეტაპი',
  };

  /// Glyph for the PLAIN-TEXT clipboard export only (`CaseExportHelper`),
  /// never for UI — the timeline's own marker is `_timelineIcon`'s monochrome
  /// `IconData` (M9b). Renamed from `icon` at M11b, which is also the
  /// CORRECTION to the M10b hand-over note calling this member orphaned: it
  /// has exactly one reader, and deleting it at M12 would break the export.
  String get exportGlyph => switch (this) {
    past => '✓',
    deadline => '⏰',
    milestone => '⭐',
  };
}

/// Risk severity level.
enum RiskSeverity {
  high,
  medium,
  low;

  String get displayNameKa => switch (this) {
    high => 'მაღალი',
    medium => 'საშუალო',
    low => 'დაბალი',
  };
}

/// Action item priority.
enum ActionPriority {
  high,
  medium,
  low;

  String get displayNameKa => switch (this) {
    high => 'მაღალი',
    medium => 'საშუალო',
    low => 'დაბალი',
  };
}

/// Trust level for AI messages.
enum TrustLevel {
  verified,
  interpretation,
  guidance;

  String get displayNameKa => switch (this) {
    verified => 'დადასტურებული',
    interpretation => 'ინტერპრეტაცია',
    guidance => 'ზოგადი მითითება',
  };
}
