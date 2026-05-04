import 'package:dio/dio.dart';
import 'package:themasteroflaw/src/src.dart';

abstract class ThemasteroflawRestApiExceptionTranslator extends HttpClientException {
  static HttpClientException translateToHttpClientException(DioException exception) {
    if (exception.response != null) {
      return translateResponseError(response: exception.response!, exceptionMessage: exception.message);
    } else {
      return _translateNetworkError(exception);
    }
  }

  static String? getErrorCodeFromResponse({required Response<dynamic> response}) {
    final data = response.data;
    if (data is Map && data.containsKey('errorCode')) {
      return data['errorCode'].toString();
    }

    return null;
  }

  static UnsuccessfulResponseException translateResponseError({
    required Response<dynamic> response,
    String? exceptionMessage,
  }) {
    if (response.statusCode == null) {
      return UnsuccessfulResponseException(errorCode: 'Unknown Dio Exception');
    }

    final message = response.data['message']?.toString();
    final errorCode = response.data['errorCode']?.toString();

    final uri = response.requestOptions.uri.toString();

    switch (response.statusCode) {
      // Client Errors
      case 400:
        return BadRequestException(message: message, errorCode: errorCode, data: response.data, uri: uri);
      case 401:
        return UnauthorizedException(message: message, errorCode: errorCode, data: response.data, uri: uri);
      case 403:
        return ForbiddenException(message: message, errorCode: errorCode, data: response.data, uri: uri);
      case 404:
        return NotFoundException(message: message, errorCode: errorCode, data: response.data, uri: uri);
      case 409:
        return ConflictException(message: message, errorCode: errorCode, data: response.data, uri: uri);

      // Server Errors
      case 500:
        return InternalServerErrorException(message: message, errorCode: errorCode, data: response.data, uri: uri);
      case 501:
        return NotImplementedException(message: message, errorCode: errorCode, data: response.data, uri: uri);
      case 502:
        return BadGatewayException(message: message, errorCode: errorCode, data: response.data, uri: uri);
      case 503:
        return ServiceUnavailableException(message: message, errorCode: errorCode, data: response.data, uri: uri);
    }

    if (response.statusCode! >= 400 && response.statusCode! < 500) {
      return ClientErrorException(
        statusCode: response.statusCode,
        errorCode: errorCode,
        message: message ?? exceptionMessage,
        data: response.data,
        uri: response.requestOptions.uri.toString(),
      );
    }

    if (response.statusCode! >= 500) {
      return ServerErrorException(
        statusCode: response.statusCode,
        errorCode: errorCode,
        message: message ?? exceptionMessage,
        data: response.data,
        uri: response.requestOptions.uri.toString(),
      );
    }

    return UnsuccessfulResponseException(
      statusCode: response.statusCode,
      errorCode: errorCode,
      message: message ?? exceptionMessage,
      data: response.data,
      uri: response.requestOptions.uri.toString(),
    );
  }

  static NetworkException _translateNetworkError(DioException exception) {
    final uri = exception.requestOptions.uri.toString();
    switch (exception.type) {
      case DioExceptionType.connectionTimeout:
        return ConnectionTimeoutException(uri: uri);
      case DioExceptionType.receiveTimeout:
        return RecieveTimeoutException(uri: uri);
      case DioExceptionType.sendTimeout:
        return SendTimeoutException(uri: uri);
      case DioExceptionType.connectionError:
        return NoConnectionException(uri: uri);

      // ignore: no_default_cases
      default:
        return NetworkException(uri: uri, exception: exception);
    }
  }
}
