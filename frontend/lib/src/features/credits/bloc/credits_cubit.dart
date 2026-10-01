import 'dart:async';

import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';

part 'credits_state.dart';

/// Holds the user's real credit balance. Refreshes on demand (app start,
/// after a billable action, and on a 402 out-of-credits response).
class CreditsCubit extends Cubit<CreditsState> {
  final CreditsRepository _repository;
  StreamSubscription<dynamic>? _authSub;

  CreditsCubit({required CreditsRepository repository})
      : _repository = repository,
        super(const CreditsState()) {
    // A 401 means the key was cleared — reset the balance so stale credits
    // never linger across re-auth.
    _authSub = dataUpdatesHub.on<UnauthorizedEvent>().listen((_) {
      if (!isClosed) emit(const CreditsState());
    });
  }

  Future<void> load() async {
    if (isClosed) return;
    emit(state.copyWith(status: StateStatus.loading));
    final result = await _repository.getCredits();
    if (isClosed) return;
    switch (result) {
      case CreditsSuccess<int>(:final data):
        emit(state.copyWith(status: StateStatus.success, balance: data));
      case CreditsFailure<int>(:final type):
        emit(state.copyWith(status: StateStatus.failed, failureType: type));
    }
  }

  /// Optimistically reflect a known spend without a round-trip; callers should
  /// still [load] afterwards to reconcile with the server.
  void decrement(int amount) {
    final current = state.balance;
    if (current == null) return;
    if (isClosed) return;
    emit(state.copyWith(balance: (current - amount).clamp(0, current)));
  }

  @override
  Future<void> close() {
    _authSub?.cancel();
    return super.close();
  }
}
