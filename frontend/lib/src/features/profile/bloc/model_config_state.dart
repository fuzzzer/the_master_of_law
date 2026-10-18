part of 'model_config_cubit.dart';

enum ModelConfigStatus { initial, loading, ready, failed }

class ModelConfigState {
  final ModelConfigStatus status;
  final ModelConfig? config;

  /// Which tier is mid-change ('strong' | 'cheap' | 'reset'), or null.
  /// The server smoke-tests a model before accepting it, so this is seconds,
  /// not milliseconds — long enough that the row must say it is busy.
  final String? pendingTier;
  final String? error;

  const ModelConfigState({
    this.status = ModelConfigStatus.initial,
    this.config,
    this.pendingTier,
    this.error,
  });

  bool get isBusy => pendingTier != null;

  ModelConfigState copyWith({
    ModelConfigStatus? status,
    ModelConfig? config,
    String? pendingTier,
    bool clearPending = false,
    String? error,
    bool clearError = false,
  }) {
    return ModelConfigState(
      status: status ?? this.status,
      config: config ?? this.config,
      pendingTier: clearPending ? null : (pendingTier ?? this.pendingTier),
      error: clearError ? null : (error ?? this.error),
    );
  }
}
