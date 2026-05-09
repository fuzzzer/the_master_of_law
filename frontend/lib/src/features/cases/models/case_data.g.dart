// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'case_data.dart';

// **************************************************************************
// TypeAdapterGenerator
// **************************************************************************

class CaseDataAdapter extends TypeAdapter<CaseData> {
  @override
  final int typeId = 0;

  @override
  CaseData read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return CaseData(
      id: fields[0] as String,
      title: fields[1] as String,
      domainIndex: fields[2] as int,
      statusIndex: fields[3] as int,
      createdAt: fields[4] as DateTime,
      updatedAt: fields[5] as DateTime,
      facts: (fields[6] as List?)?.cast<FactData>(),
      arguments: (fields[7] as List?)?.cast<ArgumentData>(),
      evidence: (fields[8] as List?)?.cast<EvidenceData>(),
      strategy: fields[9] as StrategyData?,
      timeline: (fields[10] as List?)?.cast<TimelineEventData>(),
      risks: (fields[11] as List?)?.cast<RiskData>(),
      actionItems: (fields[12] as List?)?.cast<ActionItemData>(),
      linkedConversationIds: (fields[13] as List?)?.cast<String>(),
      linkedArticles: (fields[14] as List?)?.cast<LinkedArticleData>(),
      clarifications: (fields[15] as List?)?.cast<ClarificationData>(),
    );
  }

  @override
  void write(BinaryWriter writer, CaseData obj) {
    writer
      ..writeByte(16)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.title)
      ..writeByte(2)
      ..write(obj.domainIndex)
      ..writeByte(3)
      ..write(obj.statusIndex)
      ..writeByte(4)
      ..write(obj.createdAt)
      ..writeByte(5)
      ..write(obj.updatedAt)
      ..writeByte(6)
      ..write(obj.facts)
      ..writeByte(7)
      ..write(obj.arguments)
      ..writeByte(8)
      ..write(obj.evidence)
      ..writeByte(9)
      ..write(obj.strategy)
      ..writeByte(10)
      ..write(obj.timeline)
      ..writeByte(11)
      ..write(obj.risks)
      ..writeByte(12)
      ..write(obj.actionItems)
      ..writeByte(13)
      ..write(obj.linkedConversationIds)
      ..writeByte(14)
      ..write(obj.linkedArticles)
      ..writeByte(15)
      ..write(obj.clarifications);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is CaseDataAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

class FactDataAdapter extends TypeAdapter<FactData> {
  @override
  final int typeId = 1;

  @override
  FactData read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return FactData(
      id: fields[0] as String,
      text: fields[1] as String,
      classificationIndex: fields[2] as int,
      sourceDocumentId: fields[3] as String?,
      sourceConversationId: fields[4] as String?,
      linkedArgumentId: fields[5] as String?,
      isAiGenerated: fields[6] as bool,
      createdAt: fields[7] as DateTime,
    );
  }

  @override
  void write(BinaryWriter writer, FactData obj) {
    writer
      ..writeByte(8)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.text)
      ..writeByte(2)
      ..write(obj.classificationIndex)
      ..writeByte(3)
      ..write(obj.sourceDocumentId)
      ..writeByte(4)
      ..write(obj.sourceConversationId)
      ..writeByte(5)
      ..write(obj.linkedArgumentId)
      ..writeByte(6)
      ..write(obj.isAiGenerated)
      ..writeByte(7)
      ..write(obj.createdAt);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is FactDataAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

class ArgumentDataAdapter extends TypeAdapter<ArgumentData> {
  @override
  final int typeId = 2;

  @override
  ArgumentData read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return ArgumentData(
      id: fields[0] as String,
      title: fields[1] as String,
      explanation: fields[2] as String,
      strengthIndex: fields[3] as int,
      linkedArticleIds: (fields[4] as List?)?.cast<String>(),
      linkedFactIds: (fields[5] as List?)?.cast<String>(),
      linkedEvidenceIds: (fields[6] as List?)?.cast<String>(),
      isAiGenerated: fields[7] as bool,
      createdAt: fields[8] as DateTime,
      counterArgument: fields[9] as String?,
      counterResponse: fields[10] as String?,
    );
  }

  @override
  void write(BinaryWriter writer, ArgumentData obj) {
    writer
      ..writeByte(11)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.title)
      ..writeByte(2)
      ..write(obj.explanation)
      ..writeByte(3)
      ..write(obj.strengthIndex)
      ..writeByte(4)
      ..write(obj.linkedArticleIds)
      ..writeByte(5)
      ..write(obj.linkedFactIds)
      ..writeByte(6)
      ..write(obj.linkedEvidenceIds)
      ..writeByte(7)
      ..write(obj.isAiGenerated)
      ..writeByte(8)
      ..write(obj.createdAt)
      ..writeByte(9)
      ..write(obj.counterArgument)
      ..writeByte(10)
      ..write(obj.counterResponse);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is ArgumentDataAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

class EvidenceDataAdapter extends TypeAdapter<EvidenceData> {
  @override
  final int typeId = 3;

  @override
  EvidenceData read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return EvidenceData(
      id: fields[0] as String,
      title: fields[1] as String,
      filePath: fields[2] as String?,
      typeIndex: fields[3] as int,
      linkedFactId: fields[4] as String?,
      addedAt: fields[5] as DateTime,
    );
  }

  @override
  void write(BinaryWriter writer, EvidenceData obj) {
    writer
      ..writeByte(6)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.title)
      ..writeByte(2)
      ..write(obj.filePath)
      ..writeByte(3)
      ..write(obj.typeIndex)
      ..writeByte(4)
      ..write(obj.linkedFactId)
      ..writeByte(5)
      ..write(obj.addedAt);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is EvidenceDataAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

class StrategyDataAdapter extends TypeAdapter<StrategyData> {
  @override
  final int typeId = 4;

  @override
  StrategyData read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return StrategyData(
      primaryStrategy: fields[0] as String,
      backupStrategy: fields[1] as String?,
      fallbackPosition: fields[2] as String?,
      confidenceScore: fields[3] as int,
      supportingArgumentIds: (fields[4] as List?)?.cast<String>(),
      supportingArticleIds: (fields[5] as List?)?.cast<String>(),
      isAiGenerated: fields[6] as bool,
    );
  }

  @override
  void write(BinaryWriter writer, StrategyData obj) {
    writer
      ..writeByte(7)
      ..writeByte(0)
      ..write(obj.primaryStrategy)
      ..writeByte(1)
      ..write(obj.backupStrategy)
      ..writeByte(2)
      ..write(obj.fallbackPosition)
      ..writeByte(3)
      ..write(obj.confidenceScore)
      ..writeByte(4)
      ..write(obj.supportingArgumentIds)
      ..writeByte(5)
      ..write(obj.supportingArticleIds)
      ..writeByte(6)
      ..write(obj.isAiGenerated);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is StrategyDataAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

class TimelineEventDataAdapter extends TypeAdapter<TimelineEventData> {
  @override
  final int typeId = 5;

  @override
  TimelineEventData read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return TimelineEventData(
      id: fields[0] as String,
      date: fields[1] as DateTime,
      title: fields[2] as String,
      description: fields[3] as String?,
      typeIndex: fields[4] as int,
      isCompleted: fields[5] as bool,
    );
  }

  @override
  void write(BinaryWriter writer, TimelineEventData obj) {
    writer
      ..writeByte(6)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.date)
      ..writeByte(2)
      ..write(obj.title)
      ..writeByte(3)
      ..write(obj.description)
      ..writeByte(4)
      ..write(obj.typeIndex)
      ..writeByte(5)
      ..write(obj.isCompleted);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is TimelineEventDataAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

class RiskDataAdapter extends TypeAdapter<RiskData> {
  @override
  final int typeId = 6;

  @override
  RiskData read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return RiskData(
      id: fields[0] as String,
      description: fields[1] as String,
      severityIndex: fields[2] as int,
      mitigationSuggestion: fields[3] as String?,
      linkedArticleId: fields[4] as String?,
      isAiGenerated: fields[5] as bool,
    );
  }

  @override
  void write(BinaryWriter writer, RiskData obj) {
    writer
      ..writeByte(6)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.description)
      ..writeByte(2)
      ..write(obj.severityIndex)
      ..writeByte(3)
      ..write(obj.mitigationSuggestion)
      ..writeByte(4)
      ..write(obj.linkedArticleId)
      ..writeByte(5)
      ..write(obj.isAiGenerated);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is RiskDataAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

class ActionItemDataAdapter extends TypeAdapter<ActionItemData> {
  @override
  final int typeId = 7;

  @override
  ActionItemData read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return ActionItemData(
      id: fields[0] as String,
      task: fields[1] as String,
      deadline: fields[2] as DateTime?,
      priorityIndex: fields[3] as int,
      isCompleted: fields[4] as bool,
    );
  }

  @override
  void write(BinaryWriter writer, ActionItemData obj) {
    writer
      ..writeByte(5)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.task)
      ..writeByte(2)
      ..write(obj.deadline)
      ..writeByte(3)
      ..write(obj.priorityIndex)
      ..writeByte(4)
      ..write(obj.isCompleted);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is ActionItemDataAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

class LinkedArticleDataAdapter extends TypeAdapter<LinkedArticleData> {
  @override
  final int typeId = 8;

  @override
  LinkedArticleData read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return LinkedArticleData(
      articleId: fields[0] as String,
      title: fields[1] as String,
      codeName: fields[2] as String,
      snippet: fields[3] as String,
      savedAt: fields[4] as DateTime,
    );
  }

  @override
  void write(BinaryWriter writer, LinkedArticleData obj) {
    writer
      ..writeByte(5)
      ..writeByte(0)
      ..write(obj.articleId)
      ..writeByte(1)
      ..write(obj.title)
      ..writeByte(2)
      ..write(obj.codeName)
      ..writeByte(3)
      ..write(obj.snippet)
      ..writeByte(4)
      ..write(obj.savedAt);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is LinkedArticleDataAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}

class ClarificationDataAdapter extends TypeAdapter<ClarificationData> {
  @override
  final int typeId = 9;

  @override
  ClarificationData read(BinaryReader reader) {
    final numOfFields = reader.readByte();
    final fields = <int, dynamic>{
      for (int i = 0; i < numOfFields; i++) reader.readByte(): reader.read(),
    };
    return ClarificationData(
      id: fields[0] as String,
      question: fields[1] as String,
      isResolved: fields[2] as bool,
      resolution: fields[3] as String?,
    );
  }

  @override
  void write(BinaryWriter writer, ClarificationData obj) {
    writer
      ..writeByte(4)
      ..writeByte(0)
      ..write(obj.id)
      ..writeByte(1)
      ..write(obj.question)
      ..writeByte(2)
      ..write(obj.isResolved)
      ..writeByte(3)
      ..write(obj.resolution);
  }

  @override
  int get hashCode => typeId.hashCode;

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is ClarificationDataAdapter &&
          runtimeType == other.runtimeType &&
          typeId == other.typeId;
}
