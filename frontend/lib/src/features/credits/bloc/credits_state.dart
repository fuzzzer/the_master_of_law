part of 'credits_cubit.dart';

class CreditsState {
  final StateStatus status;
  final int? balance;
  final CreditsFailureType? failureType;

  const CreditsState({
    this.status = StateStatus.initial,
    this.balance,
    this.failureType,
  });

  bool get hasBalance => balance != null;

  CreditsState copyWith({
    StateStatus? status,
    int? balance,
    CreditsFailureType? failureType,
  }) {
    return CreditsState(
      status: status ?? this.status,
      balance: balance ?? this.balance,
      failureType: failureType ?? this.failureType,
    );
  }
}
