import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

part 'case_detail_state.dart';

/// Manages a single case's detail data and sub-section editing.
class CaseDetailCubit extends Cubit<CaseDetailState> {
  final CaseRepository _repository;

  CaseDetailCubit({required CaseRepository repository})
      : _repository = repository,
        super(const CaseDetailState());

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

  // ── Conversations ─────────────────────────────────────────────────

  Future<void> linkConversation(String conversationId) async {
    final caseData = state.caseData;
    if (caseData == null) return;
    if (!caseData.linkedConversationIds.contains(conversationId)) {
      caseData.linkedConversationIds.add(conversationId);
      await _save(caseData);
    }
  }

  // ── Private helpers ────────────────────────────────────────────────

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
