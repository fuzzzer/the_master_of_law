import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

part 'feedback_state.dart';

class FeedbackCubit extends Cubit<FeedbackState> {
  final FeedbackRepository _repository;

  FeedbackCubit({required FeedbackRepository repository})
      : _repository = repository,
        super(const FeedbackState());

  Future<void> submitFeedback(FeedbackSubmitRequestParameters params) async {
    emit(state.copyWith(status: StateStatus.loading));
    final result = await _repository.submitFeedback(params);
    switch (result) {
      case FeedbackSuccess<FeedbackSubmitResponseData>(:final data):
        emit(state.copyWith(status: StateStatus.success, lastSubmittedId: data.id));
      case FeedbackFailure<FeedbackSubmitResponseData>(:final type):
        emit(state.copyWith(status: StateStatus.failed, failureType: type));
    }
  }

  void reset() {
    emit(const FeedbackState());
  }
}
