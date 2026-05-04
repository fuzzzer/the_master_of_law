import 'package:themasteroflaw/src/core/services/http_client/http_client.dart';

//TODO setup custom unsuccessful your service exception
class UnsuccessfulthemasteroflawResponseException extends UnsuccessfulResponseException {
  UnsuccessfulthemasteroflawResponseException({
    super.message,
    super.uri,
    super.statusCode,
    super.errorCode,
    super.data,
  });
}
