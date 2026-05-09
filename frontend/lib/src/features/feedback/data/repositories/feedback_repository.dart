import 'package:themasteroflaw/src/src.dart';

sealed class FeedbackResult<T> {
  const FeedbackResult();
}

class FeedbackSuccess<T> extends FeedbackResult<T> {
  final T data;
  const FeedbackSuccess(this.data);
}

class FeedbackFailure<T> extends FeedbackResult<T> {
  final FeedbackFailureType type;
  final String? message;
  const FeedbackFailure({required this.type, this.message});
}

enum FeedbackFailureType { network, unauthorized, validation, serverError, unknown }

class FeedbackRepository {
  final FeedbackRemoteDataSource _remoteDataSource;

  FeedbackRepository({required FeedbackRemoteDataSource remoteDataSource})
    : _remoteDataSource = remoteDataSource;

  Future<FeedbackResult<FeedbackSubmitResponseData>> submitFeedback(
    FeedbackSubmitRequestParameters params,
  ) async {
    try {
      final data = await _remoteDataSource.submitFeedback(params);
      return FeedbackSuccess(FeedbackSubmitResponseData.fromMap(data));
    } on HttpClientException catch (e) {
      return FeedbackFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return FeedbackFailure(type: FeedbackFailureType.unknown, message: e.toString());
    }
  }

  FeedbackFailureType _mapHttpError(HttpClientException e) {
    return switch (e) {
      UnauthorizedException() => FeedbackFailureType.unauthorized,
      NoConnectionException() => FeedbackFailureType.network,
      ClientErrorException() => FeedbackFailureType.validation,
      _ => FeedbackFailureType.serverError,
    };
  }
}
