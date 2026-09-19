part of 'case_detail_cubit.dart';

class CaseDetailState {
  final StateStatus status;
  final CaseData? caseData;

  /// True when the most recent edit failed to persist. The UI should surface a
  /// retry/snackbar so edits don't silently diverge from storage.
  final bool saveFailed;

  const CaseDetailState({
    this.status = StateStatus.initial,
    this.caseData,
    this.saveFailed = false,
  });

  CaseDetailState copyWith({
    StateStatus? status,
    CaseData? caseData,
    bool? saveFailed,
  }) {
    return CaseDetailState(
      status: status ?? this.status,
      caseData: caseData ?? this.caseData,
      saveFailed: saveFailed ?? this.saveFailed,
    );
  }
}
