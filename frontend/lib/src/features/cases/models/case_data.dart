import 'package:hive/hive.dart';

import 'enums.dart';

part 'case_data.g.dart';

/// Complete case data model — the central organizing unit.
/// Stored locally in Hive. Everything links to a case.
@HiveType(typeId: 0)
class CaseData extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  String title;

  @HiveField(2)
  final int domainIndex;

  @HiveField(3)
  int statusIndex;

  @HiveField(4)
  final DateTime createdAt;

  @HiveField(5)
  DateTime updatedAt;

  @HiveField(6)
  final List<FactData> facts;

  @HiveField(7)
  final List<ArgumentData> arguments;

  @HiveField(8)
  final List<EvidenceData> evidence;

  @HiveField(9)
  StrategyData? strategy;

  @HiveField(10)
  final List<TimelineEventData> timeline;

  @HiveField(11)
  final List<RiskData> risks;

  @HiveField(12)
  final List<ActionItemData> actionItems;

  @HiveField(13)
  final List<String> linkedConversationIds;

  @HiveField(14)
  final List<LinkedArticleData> linkedArticles;

  @HiveField(15)
  final List<ClarificationData> clarifications;

  CaseData({
    required this.id,
    required this.title,
    required this.domainIndex,
    this.statusIndex = 0,
    required this.createdAt,
    required this.updatedAt,
    List<FactData>? facts,
    List<ArgumentData>? arguments,
    List<EvidenceData>? evidence,
    this.strategy,
    List<TimelineEventData>? timeline,
    List<RiskData>? risks,
    List<ActionItemData>? actionItems,
    List<String>? linkedConversationIds,
    List<LinkedArticleData>? linkedArticles,
    List<ClarificationData>? clarifications,
  }) : facts = facts ?? [],
       arguments = arguments ?? [],
       evidence = evidence ?? [],
       timeline = timeline ?? [],
       risks = risks ?? [],
       actionItems = actionItems ?? [],
       linkedConversationIds = linkedConversationIds ?? [],
       linkedArticles = linkedArticles ?? [],
       clarifications = clarifications ?? [];

  LegalDomain get domain => LegalDomain.values[domainIndex];
  set domain(LegalDomain d) => domainIndex == d.index;

  CaseStatus get status => CaseStatus.values[statusIndex];

  /// Case completeness as a percentage (0–100).
  int get completenessPercent {
    var filled = 0;
    const total = 7;
    if (facts.isNotEmpty) filled++;
    if (arguments.isNotEmpty) filled++;
    if (evidence.isNotEmpty) filled++;
    if (strategy != null) filled++;
    if (timeline.isNotEmpty) filled++;
    if (risks.isNotEmpty) filled++;
    if (actionItems.isNotEmpty) filled++;
    return ((filled / total) * 100).round();
  }

  /// Case strength score (0-100) based on data quality.
  int get strengthScore {
    var score = 0;
    // Facts coverage
    final favorableCount = facts.where((f) => f.classificationIndex == FactClassification.favorable.index).length;
    if (favorableCount >= 3) {
      score += 20;
    } else if (favorableCount >= 1) {
      score += 10;
    }
    // Arguments
    final strongArgs = arguments.where((a) => a.strengthIndex == ArgumentStrength.strong.index).length;
    if (strongArgs >= 2) {
      score += 25;
    } else if (strongArgs >= 1) {
      score += 15;
    } else if (arguments.isNotEmpty) {
      score += 5;
    }
    // Evidence
    if (evidence.length >= 3) {
      score += 20;
    } else if (evidence.isNotEmpty) {
      score += 10;
    }
    // Strategy
    if (strategy != null) score += 15;
    // Timeline
    if (timeline.isNotEmpty) score += 10;
    // Risks
    if (risks.isNotEmpty) score += 10;
    return score.clamp(0, 100);
  }
}

/// A single fact within a case.
@HiveType(typeId: 1)
class FactData extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  String text;

  @HiveField(2)
  int classificationIndex;

  @HiveField(3)
  String? sourceDocumentId;

  @HiveField(4)
  String? sourceConversationId;

  @HiveField(5)
  String? linkedArgumentId;

  @HiveField(6)
  final bool isAiGenerated;

  @HiveField(7)
  final DateTime createdAt;

  FactData({
    required this.id,
    required this.text,
    required this.classificationIndex,
    this.sourceDocumentId,
    this.sourceConversationId,
    this.linkedArgumentId,
    this.isAiGenerated = false,
    required this.createdAt,
  });

  FactClassification get classification => FactClassification.values[classificationIndex];
}

/// A legal argument supporting the case.
@HiveType(typeId: 2)
class ArgumentData extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  String title;

  @HiveField(2)
  String explanation;

  @HiveField(3)
  int strengthIndex;

  @HiveField(4)
  final List<String> linkedArticleIds;

  @HiveField(5)
  final List<String> linkedFactIds;

  @HiveField(6)
  final List<String> linkedEvidenceIds;

  @HiveField(7)
  final bool isAiGenerated;

  @HiveField(8)
  final DateTime createdAt;

  @HiveField(9)
  String? counterArgument;

  @HiveField(10)
  String? counterResponse;

  ArgumentData({
    required this.id,
    required this.title,
    required this.explanation,
    required this.strengthIndex,
    List<String>? linkedArticleIds,
    List<String>? linkedFactIds,
    List<String>? linkedEvidenceIds,
    this.isAiGenerated = false,
    required this.createdAt,
    this.counterArgument,
    this.counterResponse,
  }) : linkedArticleIds = linkedArticleIds ?? [],
       linkedFactIds = linkedFactIds ?? [],
       linkedEvidenceIds = linkedEvidenceIds ?? [];

  ArgumentStrength get strength => ArgumentStrength.values[strengthIndex];
}

/// Attached evidence item.
@HiveType(typeId: 3)
class EvidenceData extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  String title;

  @HiveField(2)
  String? filePath;

  @HiveField(3)
  int typeIndex;

  @HiveField(4)
  String? linkedFactId;

  @HiveField(5)
  final DateTime addedAt;

  EvidenceData({
    required this.id,
    required this.title,
    this.filePath,
    required this.typeIndex,
    this.linkedFactId,
    required this.addedAt,
  });

  EvidenceType get type => EvidenceType.values[typeIndex];
}

/// Defense strategy data.
@HiveType(typeId: 4)
class StrategyData extends HiveObject {
  @HiveField(0)
  String primaryStrategy;

  @HiveField(1)
  String? backupStrategy;

  @HiveField(2)
  String? fallbackPosition;

  @HiveField(3)
  int confidenceScore;

  @HiveField(4)
  final List<String> supportingArgumentIds;

  @HiveField(5)
  final List<String> supportingArticleIds;

  @HiveField(6)
  final bool isAiGenerated;

  StrategyData({
    required this.primaryStrategy,
    this.backupStrategy,
    this.fallbackPosition,
    this.confidenceScore = 0,
    List<String>? supportingArgumentIds,
    List<String>? supportingArticleIds,
    this.isAiGenerated = false,
  }) : supportingArgumentIds = supportingArgumentIds ?? [],
       supportingArticleIds = supportingArticleIds ?? [];
}

/// A timeline event or deadline.
@HiveType(typeId: 5)
class TimelineEventData extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  DateTime date;

  @HiveField(2)
  String title;

  @HiveField(3)
  String? description;

  @HiveField(4)
  int typeIndex;

  @HiveField(5)
  bool isCompleted;

  TimelineEventData({
    required this.id,
    required this.date,
    required this.title,
    this.description,
    required this.typeIndex,
    this.isCompleted = false,
  });

  TimelineEventType get type => TimelineEventType.values[typeIndex];

  /// Days until this deadline (negative = overdue).
  int get daysRemaining => date.difference(DateTime.now()).inDays;
}

/// A risk or weakness in the case.
@HiveType(typeId: 6)
class RiskData extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  String description;

  @HiveField(2)
  int severityIndex;

  @HiveField(3)
  String? mitigationSuggestion;

  @HiveField(4)
  String? linkedArticleId;

  @HiveField(5)
  final bool isAiGenerated;

  RiskData({
    required this.id,
    required this.description,
    required this.severityIndex,
    this.mitigationSuggestion,
    this.linkedArticleId,
    this.isAiGenerated = false,
  });

  RiskSeverity get severity => RiskSeverity.values[severityIndex];
}

/// A to-do action item.
@HiveType(typeId: 7)
class ActionItemData extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  String task;

  @HiveField(2)
  DateTime? deadline;

  @HiveField(3)
  int priorityIndex;

  @HiveField(4)
  bool isCompleted;

  ActionItemData({
    required this.id,
    required this.task,
    this.deadline,
    required this.priorityIndex,
    this.isCompleted = false,
  });

  ActionPriority get priority => ActionPriority.values[priorityIndex];
}

/// A law article saved to a case for reference.
@HiveType(typeId: 8)
class LinkedArticleData extends HiveObject {
  @HiveField(0)
  final String articleId;

  @HiveField(1)
  final String title;

  @HiveField(2)
  final String codeName;

  @HiveField(3)
  final String snippet;

  @HiveField(4)
  final DateTime savedAt;

  LinkedArticleData({
    required this.articleId,
    required this.title,
    required this.codeName,
    this.snippet = '',
    required this.savedAt,
  });
}

/// Information the AI flagged as unknown/uncertain — needs user action to clarify.
@HiveType(typeId: 9)
class ClarificationData extends HiveObject {
  @HiveField(0)
  final String id;

  @HiveField(1)
  String question;

  @HiveField(2)
  bool isResolved;

  @HiveField(3)
  String? resolution;

  ClarificationData({
    required this.id,
    required this.question,
    this.isResolved = false,
    this.resolution,
  });
}
