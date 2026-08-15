import 'package:fuzzzy_law/src/src.dart';

class QuestionnaireRepository {
  final QuestionnaireRemoteDataSource _remoteDataSource;

  QuestionnaireRepository({required QuestionnaireRemoteDataSource remoteDataSource})
    : _remoteDataSource = remoteDataSource;

  Future<ConsultationResult<Map<String, dynamic>>> generateQuestionnaire({
    required String conversationId,
    required String domain,
    required String userDescription,
  }) async {
    try {
      final data = await _remoteDataSource.generateQuestionnaire(
        conversationId: conversationId,
        domain: domain,
        userDescription: userDescription,
      );
      return ConsultationSuccess(data);
    } on HttpClientException catch (e) {
      return ConsultationFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return ConsultationFailure(type: ConsultationFailureType.unknown, message: e.toString());
    }
  }

  Future<ConsultationResult<Map<String, dynamic>>> getQuestionnaire(String conversationId) async {
    try {
      final data = await _remoteDataSource.getQuestionnaire(conversationId);
      return ConsultationSuccess(data);
    } on HttpClientException catch (e) {
      return ConsultationFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return ConsultationFailure(type: ConsultationFailureType.unknown, message: e.toString());
    }
  }

  Future<ConsultationResult<Map<String, dynamic>>> submitAnswer({
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
      return ConsultationSuccess(data);
    } on HttpClientException catch (e) {
      return ConsultationFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return ConsultationFailure(type: ConsultationFailureType.unknown, message: e.toString());
    }
  }

  Future<ConsultationResult<Map<String, dynamic>>> skipRemaining(String conversationId) async {
    try {
      final data = await _remoteDataSource.skipRemaining(conversationId);
      return ConsultationSuccess(data);
    } on HttpClientException catch (e) {
      return ConsultationFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return ConsultationFailure(type: ConsultationFailureType.unknown, message: e.toString());
    }
  }

  Future<ConsultationResult<Map<String, dynamic>>> extractFromNarrative({
    required String conversationId,
    required String domain,
    required String narrative,
  }) async {
    try {
      final data = await _remoteDataSource.extractFromNarrative(
        conversationId: conversationId,
        domain: domain,
        narrative: narrative,
      );
      return ConsultationSuccess(data);
    } on HttpClientException catch (e) {
      return ConsultationFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return ConsultationFailure(type: ConsultationFailureType.unknown, message: e.toString());
    }
  }

  ConsultationFailureType _mapHttpError(HttpClientException e) {
    return switch (e) {
      UnauthorizedException() => ConsultationFailureType.unauthorized,
      NotFoundException() => ConsultationFailureType.notFound,
      NoConnectionException() => ConsultationFailureType.network,
      _ => ConsultationFailureType.serverError,
    };
  }
}
