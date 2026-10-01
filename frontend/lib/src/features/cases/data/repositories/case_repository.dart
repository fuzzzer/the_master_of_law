import 'package:fuzzzy_law/src/src.dart';

/// Sealed result type for case repository operations.
sealed class CaseResult<T> {
  const CaseResult();
}

class CaseSuccess<T> extends CaseResult<T> {
  final T data;
  const CaseSuccess(this.data);
}

class CaseFailure<T> extends CaseResult<T> {
  final CaseFailureType type;
  final String? message;
  const CaseFailure({required this.type, this.message});
}

enum CaseFailureType { notFound, storageError, unknown }

/// Repository for case data operations.
/// Returns sealed [CaseResult] — never throws.
class CaseRepository {
  final CaseLocalDataSource _localDataSource;

  CaseRepository({required CaseLocalDataSource localDataSource})
      : _localDataSource = localDataSource;

  Future<CaseResult<List<CaseData>>> getAllCases() async {
    try {
      final cases = await _localDataSource.getAllCases();
      return CaseSuccess(cases);
    } catch (e) {
      return CaseFailure(type: CaseFailureType.storageError, message: e.toString());
    }
  }

  Future<CaseResult<CaseData>> getCaseById(String id) async {
    try {
      final caseData = await _localDataSource.getCaseById(id);
      if (caseData == null) {
        return const CaseFailure(type: CaseFailureType.notFound);
      }
      return CaseSuccess(caseData);
    } catch (e) {
      return CaseFailure(type: CaseFailureType.storageError, message: e.toString());
    }
  }

  Future<CaseResult<CaseData>> createCase({
    required String title,
    required LegalDomain domain,
  }) async {
    try {
      final now = DateTime.now();
      final caseData = CaseData(
        id: now.millisecondsSinceEpoch.toString(),
        title: title,
        domainIndex: domain.index,
        createdAt: now,
        updatedAt: now,
      );
      await _localDataSource.saveCase(caseData);
      return CaseSuccess(caseData);
    } catch (e) {
      return CaseFailure(type: CaseFailureType.storageError, message: e.toString());
    }
  }

  Future<CaseResult<CaseData>> updateCase(CaseData caseData) async {
    try {
      caseData.updatedAt = DateTime.now();
      await _localDataSource.saveCase(caseData);
      return CaseSuccess(caseData);
    } catch (e) {
      return CaseFailure(type: CaseFailureType.storageError, message: e.toString());
    }
  }

  Future<CaseResult<void>> deleteCase(String id) async {
    try {
      await _localDataSource.deleteCase(id);
      return const CaseSuccess(null);
    } catch (e) {
      return CaseFailure(type: CaseFailureType.storageError, message: e.toString());
    }
  }

  Future<CaseResult<CaseData>> importCaseData(Map<String, dynamic> json) async {
    try {
      final now = DateTime.now();
      
      final facts = <FactData>[];
      final factsJson = json['facts'] as Map<String, dynamic>? ?? {};
      int factId = 0;
      for (final entry in factsJson.entries) {
        if (entry.value != null && entry.value.toString().isNotEmpty) {
           facts.add(FactData(
             id: 'fact_${now.millisecondsSinceEpoch}_${factId++}',
             text: '${entry.key}: ${entry.value}',
             classificationIndex: FactClassification.neutral.index,
             createdAt: now,
             isAiGenerated: true,
           ));
        }
      }

      final evidenceList = <EvidenceData>[];
      final evJson = json['evidence'] as Map<String, dynamic>? ?? {};
      int evId = 0;
      for (final item in (evJson['has'] as List<dynamic>? ?? [])) {
         evidenceList.add(EvidenceData(
           id: 'ev_${now.millisecondsSinceEpoch}_${evId++}',
           title: item.toString(),
           typeIndex: EvidenceType.document.index,
           addedAt: now,
         ));
      }
      for (final item in (evJson['needs'] as List<dynamic>? ?? [])) {
         evidenceList.add(EvidenceData(
           id: 'ev_${now.millisecondsSinceEpoch}_${evId++}',
           title: '[საჭიროა] $item',
           typeIndex: EvidenceType.other.index,
           addedAt: now,
         ));
      }

      final argsList = <ArgumentData>[];
      int argId = 0;
      final defStrats = json['defense_strategies'] as List<dynamic>? ?? [];
      StrategyData? strategy;
      
      if (defStrats.isNotEmpty) {
        final firstStrat = defStrats.first as Map<String, dynamic>? ?? {};
        strategy = StrategyData(
          primaryStrategy: firstStrat['name']?.toString() ?? 'სტრატეგია',
          backupStrategy: defStrats.length > 1 ? (defStrats[1] as Map<String,dynamic>)['name']?.toString() : null,
          isAiGenerated: true,
        );
        for (final strat in defStrats) {
           final map = strat as Map<String, dynamic>;
           argsList.add(ArgumentData(
             id: 'arg_${now.millisecondsSinceEpoch}_${argId++}',
             title: map['name']?.toString() ?? 'სტრატეგია',
             explanation: 'წარმატების შანსი: ${map['success_likelihood']}\nრისკი: ${map['risk_level']}\n\n${map['how_it_works']}',
             strengthIndex: ArgumentStrength.strong.index,
             createdAt: now,
             isAiGenerated: true,
           ));
        }
      }

      final prosArgs = json['prosecution_args'] as List<dynamic>? ?? [];
      for (final pArg in prosArgs) {
         final map = pArg as Map<String, dynamic>;
         argsList.add(ArgumentData(
           id: 'arg_${now.millisecondsSinceEpoch}_${argId++}',
           title: 'მოწინააღმდეგის არგუმენტი',
           explanation: map['argument']?.toString() ?? '',
           counterArgument: map['counter']?.toString(),
           strengthIndex: ArgumentStrength.weak.index,
           createdAt: now,
           isAiGenerated: true,
         ));
      }

      final actionsList = <ActionItemData>[];
      int actId = 0;
      final checklist = json['action_checklist'] as List<dynamic>? ?? [];
      for (final task in checklist) {
         final map = task as Map<String, dynamic>;
         actionsList.add(ActionItemData(
           id: 'act_${now.millisecondsSinceEpoch}_${actId++}',
           task: map['action']?.toString() ?? '',
           priorityIndex: ActionPriority.high.index,
           isCompleted: map['done'] == true,
         ));
      }

      final linkedArts = <LinkedArticleData>[];
      final citations = json['citations'] as List<dynamic>? ?? [];
      for (final cit in citations) {
         final map = cit as Map<String, dynamic>;
         linkedArts.add(LinkedArticleData(
           articleId: map['article']?.toString() ?? '',
           title: map['article']?.toString() ?? '',
           codeName: map['code']?.toString() ?? '',
           snippet: map['text']?.toString() ?? '',
           savedAt: now,
         ));
      }

      final clarifications = <ClarificationData>[];
      int clarId = 0;
      final unclear = json['unclear_items'] as List<dynamic>? ?? [];
      for (final item in unclear) {
         clarifications.add(ClarificationData(
           id: 'clar_${now.millisecondsSinceEpoch}_${clarId++}',
           question: item.toString(),
         ));
      }

      final caseData = CaseData(
        id: json['id']?.toString() ?? now.millisecondsSinceEpoch.toString(),
        title: json['title']?.toString() ?? 'ახალი საქმე',
        domainIndex: LegalDomain.civil.index,
        createdAt: now,
        updatedAt: now,
        facts: facts,
        evidence: evidenceList,
        arguments: argsList,
        strategy: strategy,
        actionItems: actionsList,
        linkedArticles: linkedArts,
        clarifications: clarifications,
      );

      await _localDataSource.saveCase(caseData);
      return CaseSuccess(caseData);
    } catch (e) {
      return CaseFailure(type: CaseFailureType.storageError, message: e.toString());
    }
  }
}
