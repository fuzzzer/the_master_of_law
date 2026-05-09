import 'package:themasteroflaw/src/src.dart';

sealed class ConsultationResult<T> {
  const ConsultationResult();
}

class ConsultationSuccess<T> extends ConsultationResult<T> {
  final T data;
  const ConsultationSuccess(this.data);
}

class ConsultationFailure<T> extends ConsultationResult<T> {
  final ConsultationFailureType type;
  final String? message;
  const ConsultationFailure({required this.type, this.message});
}

enum ConsultationFailureType { network, unauthorized, noCredits, notFound, serverError, unknown }

class ConsultationRepository {
  final ConsultationRemoteDataSource _remoteDataSource;

  ConsultationRepository({required ConsultationRemoteDataSource remoteDataSource})
    : _remoteDataSource = remoteDataSource;

  Future<ConsultationResult<Map<String, dynamic>>> createConversation({String? caseId}) async {
    try {
      final data = await _remoteDataSource.createConversation(caseId: caseId);
      return ConsultationSuccess(data);
    } on HttpClientException catch (e) {
      return ConsultationFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return ConsultationFailure(type: ConsultationFailureType.unknown, message: e.toString());
    }
  }

  Future<ConsultationResult<List<dynamic>>> getConversations() async {
    try {
      final data = await _remoteDataSource.getConversations();
      return ConsultationSuccess(data);
    } on HttpClientException catch (e) {
      return ConsultationFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return ConsultationFailure(type: ConsultationFailureType.unknown, message: e.toString());
    }
  }

  Future<ConsultationResult<Map<String, dynamic>>> getConversation(String id) async {
    try {
      final data = await _remoteDataSource.getConversation(id);
      return ConsultationSuccess(data);
    } on HttpClientException catch (e) {
      return ConsultationFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return ConsultationFailure(type: ConsultationFailureType.unknown, message: e.toString());
    }
  }

  Future<ConsultationResult<void>> deleteConversation(String id) async {
    try {
      await _remoteDataSource.deleteConversation(id);
      return const ConsultationSuccess(null);
    } on HttpClientException catch (e) {
      return ConsultationFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return ConsultationFailure(type: ConsultationFailureType.unknown, message: e.toString());
    }
  }

  Future<ConsultationResult<Map<String, dynamic>>> sendMessage({
    required String conversationId,
    required String message,
    Map<String, dynamic>? ragConfig,
    String mode = 'chat',
    String? caseContext,
  }) async {
    try {
      final data = await _remoteDataSource.sendMessage(
        conversationId: conversationId,
        message: message,
        ragConfig: ragConfig,
        mode: mode,
        caseContext: caseContext,
      );
      return ConsultationSuccess(data);
    } on HttpClientException catch (e) {
      return ConsultationFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return ConsultationFailure(type: ConsultationFailureType.unknown, message: e.toString());
    }
  }

  Future<ConsultationResult<Map<String, dynamic>>> buildCaseFile({
    required String conversationId,
  }) async {
    try {
      final data = await _remoteDataSource.buildCaseFile(
        conversationId: conversationId,
      );
      return ConsultationSuccess(data);
    } on HttpClientException catch (e) {
      return ConsultationFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return ConsultationFailure(type: ConsultationFailureType.unknown, message: e.toString());
    }
  }

  ConsultationFailureType _mapHttpError(HttpClientException e) {
    if (e is UnsuccessfulResponseException && e.statusCode == 402) {
      return ConsultationFailureType.noCredits;
    }
    return switch (e) {
      UnauthorizedException() => ConsultationFailureType.unauthorized,
      NotFoundException() => ConsultationFailureType.notFound,
      NoConnectionException() => ConsultationFailureType.network,
      _ => ConsultationFailureType.serverError,
    };
  }
}
