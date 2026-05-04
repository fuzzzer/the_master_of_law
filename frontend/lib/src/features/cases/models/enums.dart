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

  String get emoji => switch (this) {
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

  String get icon => switch (this) {
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
