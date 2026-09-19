import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';

part 'model_config_state.dart';

/// Owns the two model tiers shown on the profile screen.
///
/// The selection is PERSONAL: the server validates a model against the user's
/// own key and returns it, this stores it on the device, and the interceptor
/// attaches it to later requests. Nothing is written server-side, so one user
/// changing model cannot move anybody else — which matters because the usual
/// trigger is that user personally running out of quota on a model.
class ModelConfigCubit extends Cubit<ModelConfigState> {
  final ModelConfigRepository _repository;

  ModelConfigCubit({ModelConfigRepository? repository})
    : _repository = repository ?? ModelConfigRepository(),
      super(const ModelConfigState());

  Future<void> load() async {
    emit(state.copyWith(status: ModelConfigStatus.loading, clearError: true));
    try {
      emit(
        state.copyWith(
          status: ModelConfigStatus.ready,
          config: await _repository.fetch(),
        ),
      );
    } catch (e) {
      emit(
        state.copyWith(
          status: ModelConfigStatus.failed,
          error: _messageKa(e),
        ),
      );
    }
  }

  /// [tier] is 'strong' or 'cheap'. Held in `pendingTier` for the whole call
  /// because the server smoke-tests the model before accepting it, which
  /// takes seconds — long enough that the row must show it is working.
  Future<void> select(String tier, String model) async {
    if (state.pendingTier != null) return; // one change at a time
    emit(state.copyWith(pendingTier: tier, clearError: true));
    try {
      final config = await _repository.setModels(
        strong: tier == 'strong' ? model : null,
        cheap: tier == 'cheap' ? model : null,
      );
      // Only persisted AFTER the server validated and smoke-tested it against
      // this user's own key. Storing first would leave a model the key cannot
      // call attached to every later request.
      await sl.get<ModelPreferenceService>().save(
        strong: tier == 'strong' ? model : null,
        cheap: tier == 'cheap' ? model : null,
      );
      emit(
        state.copyWith(
          status: ModelConfigStatus.ready,
          config: config,
          clearPending: true,
        ),
      );
    } catch (e) {
      // The old value is still correct — the server rejected the change, so
      // do NOT optimistically show the new model.
      emit(state.copyWith(clearPending: true, error: _messageKa(e)));
    }
  }

  Future<void> reset() async {
    if (state.pendingTier != null) return;
    emit(state.copyWith(pendingTier: 'reset', clearError: true));
    try {
      // Cleared before the fetch so the request that reports the new effective
      // models is itself sent without the old choice attached — otherwise the
      // screen echoes back the very models the user just discarded.
      await sl.get<ModelPreferenceService>().clear();
      emit(
        state.copyWith(
          status: ModelConfigStatus.ready,
          config: await _repository.reset(),
          clearPending: true,
        ),
      );
    } catch (e) {
      emit(state.copyWith(clearPending: true, error: _messageKa(e)));
    }
  }

  /// The backend already speaks Georgian on these routes, so its message is
  /// preferred over anything invented here — it is the one that knows WHY
  /// (unknown model, unusable model, quota, forbidden).
  String _messageKa(Object e) {
    if (e is UnsuccessfulResponseException) {
      final body = e.data;
      if (body is Map && body['message'] is String) {
        return body['message'] as String;
      }
    }
    return 'მოდელების ჩატვირთვა ვერ მოხერხდა';
  }
}
