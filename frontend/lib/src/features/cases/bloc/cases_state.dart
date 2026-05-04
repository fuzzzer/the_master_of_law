part of 'cases_cubit.dart';

class CasesState {
  final StateStatus status;
  final List<CaseData> cases;

  const CasesState({
    this.status = StateStatus.initial,
    this.cases = const [],
  });

  CasesState copyWith({
    StateStatus? status,
    List<CaseData>? cases,
  }) {
    return CasesState(
      status: status ?? this.status,
      cases: cases ?? this.cases,
    );
  }
}
