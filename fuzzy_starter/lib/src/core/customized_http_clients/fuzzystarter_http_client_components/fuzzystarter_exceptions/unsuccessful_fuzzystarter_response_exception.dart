import 'package:fuzzystarter/src/core/services/http_client/http_client.dart';

//TODO setup custom unsuccessful your service exception
class UnsuccessfulFuzzystarterResponseException extends UnsuccessfulResponseException {
  UnsuccessfulFuzzystarterResponseException({
    super.message,
    super.uri,
    super.statusCode,
    super.errorCode,
    super.data,
  });
}
