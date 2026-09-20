import 'package:fuzzzy_law/src/core/services/http_client/http_client_interface/http_client_exceptions/http_client_exception.dart';

class NetworkException extends HttpClientException {
  final Object? exception;
  NetworkException({super.uri, this.exception});
}

class ConnectionTimeoutException extends NetworkException {
  ConnectionTimeoutException({super.uri});
}

class RecieveTimeoutException extends NetworkException {
  RecieveTimeoutException({super.uri});
}

class SendTimeoutException extends NetworkException {
  SendTimeoutException({super.uri});
}

class NoConnectionException extends NetworkException {
  NoConnectionException({super.uri});
}
