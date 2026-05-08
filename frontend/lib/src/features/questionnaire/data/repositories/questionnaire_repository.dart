import 'package:themasteroflaw/src/src.dart';

/// Sealed result type for questionnaire operations.
sealed class QuestionnaireResult<T> {
  const QuestionnaireResult();
}

class QuestionnaireSuccess<T> extends QuestionnaireResult<T> {
  final T data;
  const QuestionnaireSuccess(this.data);
}

class QuestionnaireFailure<T> extends QuestionnaireResult<T> {
  final QuestionnaireFailureType type;
  final String? message;
  const QuestionnaireFailure({required this.type, this.message});
}

enum QuestionnaireFailureType {
  network,
  unauthorized,
  notFound,
  serverError,
  unknown,
  validation,
}

/// Repository for questionnaire data. Never throws.
class QuestionnaireRepository {
  final QuestionnaireRemoteDataSource _remoteDataSource;

  QuestionnaireRepository({required QuestionnaireRemoteDataSource remoteDataSource})
      : _remoteDataSource = remoteDataSource;

  Future<QuestionnaireResult<Map<String, dynamic>>> generateQuestionnaire({
    required String conversationId,
    required String domain,
    String context = '',
  }) async {
    try {
      final data = await _remoteDataSource.generateQuestionnaire(
        conversationId: conversationId,
        domain: domain,
        context: context,
      );
      return QuestionnaireSuccess(data);
    } on HttpClientException catch (e) {
      return QuestionnaireFailure(
        type: _mapHttpError(e),
        message: e.toString(),
      );
    } catch (e) {
      return QuestionnaireFailure(type: QuestionnaireFailureType.unknown, message: e.toString());
    }
  }

  Future<QuestionnaireResult<Map<String, dynamic>>> getQuestionnaire(
    String conversationId,
  ) async {
    try {
      final data = await _remoteDataSource.getQuestionnaire(conversationId);
      return QuestionnaireSuccess(data);
    } on HttpClientException catch (e) {
      return QuestionnaireFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return QuestionnaireFailure(type: QuestionnaireFailureType.unknown, message: e.toString());
    }
  }

  Future<QuestionnaireResult<Map<String, dynamic>>> submitAnswer({
    required String conversationId,
    required String questionId,
    required String answer,
  }) async {
    try {
      final data = await _remoteDataSource.submitAnswer(
        conversationId: conversationId,
        questionId: questionId,
        answer: answer,
      );
      return QuestionnaireSuccess(data);
    } on HttpClientException catch (e) {
      return QuestionnaireFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return QuestionnaireFailure(type: QuestionnaireFailureType.unknown, message: e.toString());
    }
  }

  Future<QuestionnaireResult<Map<String, dynamic>>> skipQuestion({
    required String conversationId,
    required String questionId,
  }) async {
    try {
      final data = await _remoteDataSource.skipQuestion(
        conversationId: conversationId,
        questionId: questionId,
      );
      return QuestionnaireSuccess(data);
    } on HttpClientException catch (e) {
      return QuestionnaireFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return QuestionnaireFailure(type: QuestionnaireFailureType.unknown, message: e.toString());
    }
  }

  QuestionnaireFailureType _mapHttpError(HttpClientException e) {
    return switch (e) {
      UnauthorizedException() => QuestionnaireFailureType.unauthorized,
      NotFoundException() => QuestionnaireFailureType.notFound,
      NoConnectionException() => QuestionnaireFailureType.network,
      ClientErrorException() => QuestionnaireFailureType.validation,
      _ => QuestionnaireFailureType.serverError,
    };
  }
}
