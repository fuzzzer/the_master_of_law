part of 'feedback_cubit.dart';

class FeedbackState {
  final StateStatus status;
  final String? lastSubmittedId;
  final FeedbackFailureType? failureType;

  const FeedbackState({
    this.status = StateStatus.initial,
    this.lastSubmittedId,
    this.failureType,
  });

  FeedbackState copyWith({
    StateStatus? status,
    String? lastSubmittedId,
    FeedbackFailureType? failureType,
  }) => FeedbackState(
    status: status ?? this.status,
    lastSubmittedId: lastSubmittedId ?? this.lastSubmittedId,
    failureType: failureType ?? this.failureType,
  );
}
