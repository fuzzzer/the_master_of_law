//exceptions with status codes 500-599
import 'unsuccessful_reponse_exception.dart';

class ServerErrorException extends UnsuccessfulResponseException {
  ServerErrorException({
    super.statusCode,
    super.message,
    super.data,
    super.uri,
    super.errorCode,
  });

  @override
  String toString() =>
      'ServerErrorException(type: ServerErrorException, statusCode: $statusCode, message: $message, data: $data, uri: $uri)';
}

class InternalServerErrorException extends ServerErrorException {
  InternalServerErrorException({
    super.message,
    super.data,
    super.uri,
    super.errorCode,
  }) : super(statusCode: 500);
}

class NotImplementedException extends ServerErrorException {
  NotImplementedException({
    super.message,
    super.data,
    super.uri,
    super.errorCode,
  }) : super(statusCode: 501);
}

class BadGatewayException extends ServerErrorException {
  BadGatewayException({super.message, super.data, super.uri, super.errorCode}) : super(statusCode: 502);
}

class ServiceUnavailableException extends ServerErrorException {
  ServiceUnavailableException({
    super.message,
    super.data,
    super.uri,
    super.errorCode,
  }) : super(statusCode: 503);
}
