part of 'case_detail_cubit.dart';

class CaseDetailState {
  final StateStatus status;
  final CaseData? caseData;

  const CaseDetailState({
    this.status = StateStatus.initial,
    this.caseData,
  });

  CaseDetailState copyWith({
    StateStatus? status,
    CaseData? caseData,
  }) {
    return CaseDetailState(
      status: status ?? this.status,
      caseData: caseData ?? this.caseData,
    );
  }
}
