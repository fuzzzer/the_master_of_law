import '../http_client_exception.dart';

class UnsuccessfulResponseException extends HttpClientException {
  final int? statusCode;
  final String? errorCode;
  final dynamic data;

  UnsuccessfulResponseException({
    super.message,
    super.uri,
    this.statusCode,
    this.errorCode,
    this.data,
  });

  @override
  String toString() =>
      'UnsuccessfulResponseException(type: UnsuccessfulResponseException, statusCode: $statusCode, message: $message, errorCode: $errorCode, data: $data, uri: $uri)';
}
