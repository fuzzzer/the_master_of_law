import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

part 'cases_state.dart';

/// Manages the list of all cases.
class CasesCubit extends Cubit<CasesState> {
  final CaseRepository _repository;

  CasesCubit({required CaseRepository repository})
      : _repository = repository,
        super(const CasesState());

  Future<void> loadCases() async {
    emit(state.copyWith(status: StateStatus.loading));
    final result = await _repository.getAllCases();
    switch (result) {
      case CaseSuccess<List<CaseData>>(:final data):
        emit(state.copyWith(status: StateStatus.success, cases: data));
      case CaseFailure<List<CaseData>>():
        emit(state.copyWith(status: StateStatus.failed));
    }
  }

  Future<CaseData?> createCase({
    required String title,
    required LegalDomain domain,
  }) async {
    final result = await _repository.createCase(title: title, domain: domain);
    switch (result) {
      case CaseSuccess<CaseData>(:final data):
        await loadCases();
        return data;
      case CaseFailure<CaseData>():
        return null;
    }
  }

  Future<void> deleteCase(String id) async {
    await _repository.deleteCase(id);
    await loadCases();
  }
}
