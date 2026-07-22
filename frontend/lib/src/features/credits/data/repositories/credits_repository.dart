import 'package:themasteroflaw/src/src.dart';

sealed class CreditsResult<T> {
  const CreditsResult();
}

class CreditsSuccess<T> extends CreditsResult<T> {
  final T data;
  const CreditsSuccess(this.data);
}

class CreditsFailure<T> extends CreditsResult<T> {
  final CreditsFailureType type;
  final String? message;
  const CreditsFailure({required this.type, this.message});
}

enum CreditsFailureType { network, unauthorized, notFound, serverError, unknown }

class CreditsRepository {
  final CreditsRemoteDataSource _remoteDataSource;

  CreditsRepository({required CreditsRemoteDataSource remoteDataSource})
      : _remoteDataSource = remoteDataSource;

  Future<CreditsResult<int>> getCredits() async {
    try {
      final data = await _remoteDataSource.getCredits();
      // Backend may expose the balance under a few common keys.
      final raw = data['credits'] ?? data['balance'] ?? data['available'];
      final balance = raw is num ? raw.toInt() : int.tryParse(raw?.toString() ?? '');
      if (balance == null) {
        return const CreditsFailure(type: CreditsFailureType.unknown);
      }
      return CreditsSuccess(balance);
    } on HttpClientException catch (e) {
      return CreditsFailure(type: _mapHttpError(e), message: e.toString());
    } catch (e) {
      return CreditsFailure(type: CreditsFailureType.unknown, message: e.toString());
    }
  }

  CreditsFailureType _mapHttpError(HttpClientException e) {
    return switch (e) {
      UnauthorizedException() => CreditsFailureType.unauthorized,
      NotFoundException() => CreditsFailureType.notFound,
      NoConnectionException() => CreditsFailureType.network,
      ConnectionTimeoutException() => CreditsFailureType.network,
      RecieveTimeoutException() => CreditsFailureType.network,
      SendTimeoutException() => CreditsFailureType.network,
      _ => CreditsFailureType.serverError,
    };
  }
}
