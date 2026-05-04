import 'unsuccessful_reponse_exception.dart';

//exceptions with status codes 400-499
class ClientErrorException extends UnsuccessfulResponseException {
  ClientErrorException({
    super.statusCode,
    super.message,
    super.data,
    super.uri,
    super.errorCode,
  });

  @override
  String toString() =>
      'ClientErrorException(type: ClientErrorException, statusCode: $statusCode, message: $message, data: $data, uri: $uri)';
}

class BadRequestException extends ClientErrorException {
  BadRequestException({super.message, super.data, super.uri, super.errorCode}) : super(statusCode: 400);
}

class UnauthorizedException extends ClientErrorException {
  UnauthorizedException({super.message, super.data, super.uri, super.errorCode}) : super(statusCode: 401);
}

class ForbiddenException extends ClientErrorException {
  ForbiddenException({super.message, super.data, super.uri, super.errorCode}) : super(statusCode: 403);
}

class NotFoundException extends ClientErrorException {
  NotFoundException({super.message, super.data, super.uri, super.errorCode}) : super(statusCode: 404);
}

class MethodNotAllowedException extends ClientErrorException {
  MethodNotAllowedException({
    super.message,
    super.data,
    super.uri,
    super.errorCode,
  }) : super(statusCode: 405);
}

class ConflictException extends ClientErrorException {
  ConflictException({super.message, super.data, super.uri, super.errorCode}) : super(statusCode: 409);
}

class PayloadTooLargeException extends ClientErrorException {
  PayloadTooLargeException({super.message, super.data, super.errorCode}) : super(statusCode: 413);
}

class UnsupportedMediaTypeException extends ClientErrorException {
  UnsupportedMediaTypeException({super.message, super.data, super.errorCode}) : super(statusCode: 415);
}
