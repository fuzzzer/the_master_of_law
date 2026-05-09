import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

part 'case_detail_state.dart';

/// Manages a single case's detail data and sub-section editing.
class CaseDetailCubit extends Cubit<CaseDetailState> {
  final CaseRepository _repository;

  CaseDetailCubit({required CaseRepository repository}) : _repository = repository, super(const CaseDetailState());

  Future<void> loadCase(String caseId) async {
    emit(state.copyWith(status: StateStatus.loading));
    final result = await _repository.getCaseById(caseId);
    switch (result) {
      case CaseSuccess<CaseData>(:final data):
        emit(state.copyWith(status: StateStatus.success, caseData: data));
      case CaseFailure<CaseData>():
        emit(state.copyWith(status: StateStatus.failed));
    }
  }

  Future<void> updateTitle(String title) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.title = title;
    await _save(caseData);
  }

  Future<void> updateStatus(CaseStatus status) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.statusIndex = status.index;
    await _save(caseData);
  }

  // ── Facts ──────────────────────────────────────────────────────────

  Future<void> addFact(FactData fact) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.facts.add(fact);
    await _save(caseData);
  }

  Future<void> updateFact(String factId, {String? text, int? classificationIndex}) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    final fact = caseData.facts.where((f) => f.id == factId).firstOrNull;
    if (fact == null) return;
    if (text != null) fact.text = text;
    if (classificationIndex != null) fact.classificationIndex = classificationIndex;
    await _save(caseData);
  }

  Future<void> deleteFact(String factId) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.facts.removeWhere((f) => f.id == factId);
    await _save(caseData);
  }

  // ── Arguments ──────────────────────────────────────────────────────

  Future<void> addArgument(ArgumentData argument) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.arguments.add(argument);
    await _save(caseData);
  }

  Future<void> deleteArgument(String argumentId) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.arguments.removeWhere((a) => a.id == argumentId);
    await _save(caseData);
  }

  // ── Evidence ───────────────────────────────────────────────────────

  Future<void> addEvidence(EvidenceData evidence) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.evidence.add(evidence);
    await _save(caseData);
  }

  Future<void> deleteEvidence(String evidenceId) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.evidence.removeWhere((e) => e.id == evidenceId);
    await _save(caseData);
  }

  // ── Strategy ───────────────────────────────────────────────────────

  Future<void> updateStrategy(StrategyData strategy) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.strategy = strategy;
    await _save(caseData);
  }

  // ── Timeline ───────────────────────────────────────────────────────

  Future<void> addTimelineEvent(TimelineEventData event) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.timeline.add(event);
    caseData.timeline.sort((a, b) => a.date.compareTo(b.date));
    await _save(caseData);
  }

  Future<void> toggleTimelineEvent(String eventId) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    final event = caseData.timeline.where((e) => e.id == eventId).firstOrNull;
    if (event == null) return;
    event.isCompleted = !event.isCompleted;
    await _save(caseData);
  }

  Future<void> deleteTimelineEvent(String eventId) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.timeline.removeWhere((e) => e.id == eventId);
    await _save(caseData);
  }

  // ── Risks ──────────────────────────────────────────────────────────

  Future<void> addRisk(RiskData risk) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.risks.add(risk);
    await _save(caseData);
  }

  Future<void> deleteRisk(String riskId) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.risks.removeWhere((r) => r.id == riskId);
    await _save(caseData);
  }

  // ── Action Items ───────────────────────────────────────────────────

  Future<void> addActionItem(ActionItemData item) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.actionItems.add(item);
    await _save(caseData);
  }

  Future<void> toggleActionItem(String itemId) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    final item = caseData.actionItems.where((i) => i.id == itemId).firstOrNull;
    if (item == null) return;
    item.isCompleted = !item.isCompleted;
    await _save(caseData);
  }

  Future<void> deleteActionItem(String itemId) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.actionItems.removeWhere((i) => i.id == itemId);
    await _save(caseData);
  }

  Future<void> updateActionItemText(String itemId, String newText) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    final item = caseData.actionItems.where((i) => i.id == itemId).firstOrNull;
    if (item == null) return;
    item.task = newText;
    await _save(caseData);
  }

  Future<void> addClarification(ClarificationData item) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.clarifications.add(item);
    await _save(caseData);
  }

  Future<void> toggleClarification(String itemId) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    final item = caseData.clarifications.where((i) => i.id == itemId).firstOrNull;
    if (item == null) return;
    item.isResolved = !item.isResolved;
    await _save(caseData);
  }

  Future<void> updateClarificationResolution(String itemId, String resolution) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    final item = caseData.clarifications.where((i) => i.id == itemId).firstOrNull;
    if (item == null) return;
    item.resolution = resolution;
    item.isResolved = true;
    await _save(caseData);
  }

  Future<void> deleteClarification(String itemId) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.clarifications.removeWhere((i) => i.id == itemId);
    await _save(caseData);
  }

  Future<void> linkArticle(LinkedArticleData article) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    final alreadyLinked = caseData.linkedArticles.any((a) => a.articleId == article.articleId);
    if (alreadyLinked) return;
    caseData.linkedArticles.add(article);
    await _save(caseData);
  }

  Future<void> unlinkArticle(String articleId) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    caseData.linkedArticles.removeWhere((a) => a.articleId == articleId);
    await _save(caseData);
  }

  Future<void> linkConversation(String conversationId) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    if (!caseData.linkedConversationIds.contains(conversationId)) {
      caseData.linkedConversationIds.add(conversationId);
      await _save(caseData);
    }
  }

  Future<void> populateFromAiAnalysis(Map<String, dynamic> caseFileData) async {
    final caseData = state.caseData;
    if (caseData == null) return;

    caseData.facts.removeWhere((f) => f.isAiGenerated);
    caseData.arguments.removeWhere((a) => a.isAiGenerated);
    caseData.risks.removeWhere((r) => r.isAiGenerated);
    caseData.actionItems.removeWhere((a) => a.id.startsWith('ai_'));
    caseData.linkedArticles.removeWhere((a) => a.articleId.startsWith('ai_'));
    if (caseData.strategy?.isAiGenerated == true) caseData.strategy = null;

    final now = DateTime.now();
    final idBase = now.millisecondsSinceEpoch;

    final facts = caseFileData['facts'] as Map<String, dynamic>?;
    if (facts != null) {
      var i = 0;
      for (final entry in facts.entries) {
        if (entry.value != null && entry.value.toString().isNotEmpty) {
          caseData.facts.add(
            FactData(
              id: 'ai_fact_${idBase}_${i++}',
              text: '${entry.key}: ${entry.value}',
              classificationIndex: FactClassification.neutral.index,
              isAiGenerated: true,
              createdAt: now,
            ),
          );
        }
      }
    }

    final laws = caseFileData['applicable_laws'] as Map<String, dynamic>?;
    if (laws != null) {
      var i = 0;
      for (final category in ['favorable', 'against', 'neutral']) {
        final lawList = laws[category] as List<dynamic>?;
        if (lawList == null) continue;
        for (final law in lawList) {
          if (law is! Map<String, dynamic>) continue;
          caseData.linkedArticles.add(
            LinkedArticleData(
              articleId: law['article']?.toString() ?? 'ai_art_${idBase}_${i++}',
              title: '${law['code'] ?? ''} ${law['article'] ?? ''}',
              codeName: law['code']?.toString() ?? '',
              snippet: law['explanation']?.toString() ?? '',
              savedAt: now,
            ),
          );
        }
      }
    }

    final retrievedChunks = caseFileData['retrieved_chunks'] as List<dynamic>?;
    if (retrievedChunks != null) {
      var i = 0;
      for (final chunk in retrievedChunks) {
        if (chunk is! Map<String, dynamic>) continue;
        final articleId = chunk['article_number']?.toString() ?? 'rag_art_${idBase}_${i++}';
        // Avoid adding duplicates if already added by applicable_laws
        if (!caseData.linkedArticles.any((a) => a.articleId == articleId)) {
          caseData.linkedArticles.add(
            LinkedArticleData(
              articleId: articleId,
              title: '${chunk['code_name'] ?? ''} ${chunk['article_number'] ?? ''}',
              codeName: chunk['code_name']?.toString() ?? '',
              snippet: chunk['article_text']?.toString() ?? chunk['article_title']?.toString() ?? '',
              savedAt: now,
              url: chunk['article_url']?.toString(),
            ),
          );
        } else {
          // If already exists, update URL and snippet if missing
          final existing = caseData.linkedArticles.firstWhere((a) => a.articleId == articleId);
          if (existing.url == null || existing.url!.isEmpty) {
            final idx = caseData.linkedArticles.indexOf(existing);
            caseData.linkedArticles[idx] = LinkedArticleData(
              articleId: existing.articleId,
              title: existing.title,
              codeName: existing.codeName,
              snippet: existing.snippet.isEmpty ? (chunk['article_text']?.toString() ?? '') : existing.snippet,
              savedAt: existing.savedAt,
              url: chunk['article_url']?.toString(),
            );
          }
        }
      }
    }

    final strategies = caseFileData['defense_strategies'] as List<dynamic>?;
    if (strategies != null && strategies.isNotEmpty) {
      final first = strategies.first as Map<String, dynamic>;
      
      final linkedStrategyLaws = <String>[];
      final basisLaws = first['legal_basis'] as List<dynamic>?;
      if (basisLaws != null) {
        for (final law in basisLaws) {
          if (law is! String) continue;
          final fakeId = 'ai_strat_law_${idBase}_${linkedStrategyLaws.length}';
          caseData.linkedArticles.add(
            LinkedArticleData(
              articleId: fakeId,
              title: law,
              codeName: 'Strategy Law',
              savedAt: now,
            ),
          );
          linkedStrategyLaws.add(fakeId);
        }
      }

      caseData.strategy = StrategyData(
        primaryStrategy: first['name']?.toString() ?? '',
        backupStrategy: strategies.length > 1 ? (strategies[1] as Map<String, dynamic>)['name']?.toString() : null,
        confidenceScore: _parseConfidence(first['success_likelihood']?.toString()),
        isAiGenerated: true,
        supportingArticleIds: linkedStrategyLaws,
      );
    }

    final prosArgs = caseFileData['prosecution_args'] as List<dynamic>?;
    if (prosArgs != null) {
      var i = 0;
      for (final arg in prosArgs) {
        if (arg is! Map<String, dynamic>) continue;
        
        final linkedLawIds = <String>[];
        final argLaws = arg['applicable_laws'] as List<dynamic>?;
        if (argLaws != null) {
          for (final law in argLaws) {
            if (law is! String) continue;
            final fakeId = 'ai_arg_law_${idBase}_${i}_${linkedLawIds.length}';
            caseData.linkedArticles.add(
              LinkedArticleData(
                articleId: fakeId,
                title: law,
                codeName: 'Argument Law',
                savedAt: now,
              ),
            );
            linkedLawIds.add(fakeId);
          }
        }

        caseData.arguments.add(
          ArgumentData(
            id: 'ai_arg_${idBase}_${i++}',
            title: arg['argument']?.toString() ?? '',
            explanation: arg['counter']?.toString() ?? '',
            strengthIndex: ArgumentStrength.moderate.index,
            isAiGenerated: true,
            createdAt: now,
            counterArgument: arg['argument']?.toString(),
            counterResponse: arg['counter']?.toString(),
            linkedArticleIds: linkedLawIds,
          ),
        );
      }
    }

    final actions = caseFileData['action_checklist'] as List<dynamic>?;
    if (actions != null) {
      var i = 0;
      for (final action in actions) {
        if (action is! Map<String, dynamic>) continue;
        caseData.actionItems.add(
          ActionItemData(
            id: 'ai_action_${idBase}_${i++}',
            task: action['action']?.toString() ?? '',
            priorityIndex: _mapDeadlineToPriority(action['deadline']?.toString()),
            isCompleted: false,
          ),
        );
      }
    }

    final evidence = caseFileData['evidence'] as Map<String, dynamic>?;
    if (evidence != null) {
      final needs = evidence['needs'] as List<dynamic>?;
      if (needs != null) {
        var i = 0;
        for (final need in needs) {
          caseData.risks.add(
            RiskData(
              id: 'ai_risk_${idBase}_${i++}',
              description: 'მტკიცებულება საჭიროა: $need',
              severityIndex: RiskSeverity.medium.index,
              mitigationSuggestion: 'მოიპოვეთ: $need',
              isAiGenerated: true,
            ),
          );
        }
      }
    }

    final unclearItems = caseFileData['unclear_items'] as List<dynamic>?;
    if (unclearItems != null) {
      caseData.clarifications.removeWhere((c) => c.id.startsWith('ai_'));
      var i = 0;
      for (final item in unclearItems) {
        if (item is String && item.trim().isNotEmpty) {
          caseData.clarifications.add(
            ClarificationData(
              id: 'ai_clarify_${idBase}_${i++}',
              question: item,
            ),
          );
        }
      }
    }

    await _save(caseData);
  }

  int _parseConfidence(String? likelihood) {
    if (likelihood == null) return 50;
    final lower = likelihood.toLowerCase();
    if (lower.contains('high') || lower.contains('მაღალი')) return 80;
    if (lower.contains('medium') || lower.contains('საშუალო')) return 50;
    if (lower.contains('low') || lower.contains('დაბალი')) return 25;
    return 50;
  }

  int _mapDeadlineToPriority(String? deadline) {
    if (deadline == null) return ActionPriority.medium.index;
    final lower = deadline.toLowerCase();
    if (lower.contains('immediate') || lower.contains('48h')) return ActionPriority.high.index;
    if (lower.contains('3 day') || lower.contains('1 week')) return ActionPriority.high.index;
    if (lower.contains('month') || lower.contains('court')) return ActionPriority.medium.index;
    return ActionPriority.low.index;
  }

  Future<void> _save(CaseData caseData) async {
    final result = await _repository.updateCase(caseData);
    switch (result) {
      case CaseSuccess<CaseData>(:final data):
        emit(state.copyWith(caseData: data));
      case CaseFailure<CaseData>():
        break;
    }
  }
}
