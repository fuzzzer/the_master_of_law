import 'package:dio/dio.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_law/src/src.dart';

/// Answers the validate call with whatever [answer] returns or throws.
class _FakeHttpClient implements HttpClientInterface {
  _FakeHttpClient(this.answer);

  final Object Function() answer;

  @override
  Future<Response<T>> get<T>(
    Uri uri, {
    Options? options,
    CancelToken? cancelToken,
    void Function(int, int)? onReceiveProgress,
  }) async {
    final result = answer();
    if (result is Exception) throw result;
    return Response<T>(
      requestOptions: RequestOptions(path: uri.path),
      data: result as T,
      statusCode: 200,
    );
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

Future<ApiKeyCheck> _check(Object Function() answer) =>
    ApiKeyValidationDataSource(httpClient: _FakeHttpClient(answer)).validate();

void main() {
  setUpAll(() => dotenv.testLoad(fileInput: 'API_BASE_URL=http://test'));

  test('a key Google accepted is valid', () async {
    expect(
      await _check(() => <String, dynamic>{'valid': true}),
      ApiKeyCheck.valid,
    );
  });

  // The http client translates Dio's 401/403 into its own exceptions; these
  // used to fall through to "server unreachable".
  test('a 401 from the server means the key does not work', () async {
    expect(
      await _check(() => UnauthorizedException(errorCode: 'byok_key_invalid')),
      ApiKeyCheck.invalid,
    );
  });

  test('a 403 from the server means the key does not work', () async {
    expect(await _check(ForbiddenException.new), ApiKeyCheck.invalid);
  });

  test('no connection says nothing about the key', () async {
    expect(await _check(NetworkException.new), ApiKeyCheck.unreachable);
  });

  test('a server error says nothing about the key', () async {
    expect(
      await _check(InternalServerErrorException.new),
      ApiKeyCheck.unreachable,
    );
  });
}
