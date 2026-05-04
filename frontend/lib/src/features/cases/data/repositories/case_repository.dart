import 'package:themasteroflaw/src/src.dart';

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
}
