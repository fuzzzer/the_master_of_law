import 'package:fuzzzy_law/src/src.dart';

/// Sealed result type for laws operations.
sealed class LawsResult<T> {
  const LawsResult();
}

class LawsSuccess<T> extends LawsResult<T> {
  final T data;
  const LawsSuccess(this.data);
}

class LawsFailure<T> extends LawsResult<T> {
  final LawsFailureType type;
  final String? message;
  const LawsFailure({required this.type, this.message});
}

enum LawsFailureType { network, notFound, serverError, unknown }

/// Repository for laws browsing. Never throws.
class LawsRepository {
  final LawsRemoteDataSource _remoteDataSource;

  LawsRepository({required LawsRemoteDataSource remoteDataSource})
      : _remoteDataSource = remoteDataSource;

  Future<LawsResult<LawSearchResults>> searchLaws(String query) async {
    try {
      final data = await _remoteDataSource.searchLaws(query);
      return LawsSuccess(data);
    } on HttpClientException catch (e) {
      return LawsFailure(type: _mapError(e), message: e.toString());
    } catch (e) {
      return LawsFailure(type: LawsFailureType.unknown, message: e.toString());
    }
  }

  Future<LawsResult<List<LawCode>>> getCodes() async {
    try {
      final data = await _remoteDataSource.getCodes();
      return LawsSuccess(data);
    } on HttpClientException catch (e) {
      return LawsFailure(type: _mapError(e), message: e.toString());
    } catch (e) {
      return LawsFailure(type: LawsFailureType.unknown, message: e.toString());
    }
  }

  Future<LawsResult<Map<String, dynamic>>> getCodeStructure(String codeId) async {
    try {
      final data = await _remoteDataSource.getCodeStructure(codeId);
      return LawsSuccess(data);
    } on HttpClientException catch (e) {
      return LawsFailure(type: _mapError(e), message: e.toString());
    } catch (e) {
      return LawsFailure(type: LawsFailureType.unknown, message: e.toString());
    }
  }

  Future<LawsResult<LawArticleDetail>> getArticle(String articleId) async {
    try {
      final data = await _remoteDataSource.getArticle(articleId);
      return LawsSuccess(data);
    } on HttpClientException catch (e) {
      return LawsFailure(type: _mapError(e), message: e.toString());
    } catch (e) {
      return LawsFailure(type: LawsFailureType.unknown, message: e.toString());
    }
  }

  LawsFailureType _mapError(HttpClientException e) {
    return switch (e) {
      NotFoundException() => LawsFailureType.notFound,
      NoConnectionException() => LawsFailureType.network,
      _ => LawsFailureType.serverError,
    };
  }
}
