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

enum ConsultationFailureType { network, unauthorized, noCredits, rateLimited, notFound, serverError, unknown }

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

  Stream<Map<String, dynamic>> streamMessage({
    required String conversationId,
    required String message,
    Map<String, dynamic>? ragConfig,
    String mode = 'chat',
    String? caseContext,
    String? caseFileId,
  }) {
    return _remoteDataSource.streamMessage(
      conversationId: conversationId,
      message: message,
      ragConfig: ragConfig,
      mode: mode,
      caseContext: caseContext,
      caseFileId: caseFileId,
    );
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

  Future<ConsultationResult<Map<String, dynamic>>> sendAgentMessage({
    required String conversationId,
    required String message,
    required String caseFileId,
    Map<String, dynamic>? ragConfig,
  }) async {
    try {
      final data = await _remoteDataSource.sendAgentMessage(
        conversationId: conversationId,
        message: message,
        caseFileId: caseFileId,
        ragConfig: ragConfig,
      );
      return ConsultationSuccess(data);
    } on HttpClientException catch (e) {
      return ConsultationFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return ConsultationFailure(type: ConsultationFailureType.unknown, message: e.toString());
    }
  }

  Future<ConsultationResult<Map<String, dynamic>>> confirmToolAction({
    required String conversationId,
    required String confirmationId,
    required bool confirmed,
  }) async {
    try {
      final data = await _remoteDataSource.confirmToolAction(
        conversationId: conversationId,
        confirmationId: confirmationId,
        confirmed: confirmed,
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
    if (e is UnsuccessfulResponseException && e.statusCode == 429) {
      return ConsultationFailureType.rateLimited;
    }
    return switch (e) {
      UnauthorizedException() => ConsultationFailureType.unauthorized,
      TooManyRequestsException() => ConsultationFailureType.rateLimited,
      NotFoundException() => ConsultationFailureType.notFound,
      NoConnectionException() => ConsultationFailureType.network,
      ConnectionTimeoutException() => ConsultationFailureType.network,
      RecieveTimeoutException() => ConsultationFailureType.network,
      SendTimeoutException() => ConsultationFailureType.network,
      _ => ConsultationFailureType.serverError,
    };
  }
}

