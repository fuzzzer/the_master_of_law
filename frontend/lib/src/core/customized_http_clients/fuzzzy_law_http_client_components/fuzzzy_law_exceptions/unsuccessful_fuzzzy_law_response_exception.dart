import 'package:fuzzzy_law/src/core/services/http_client/http_client.dart';

//TODO setup custom unsuccessful your service exception
class UnsuccessfulFuzzzyLawResponseException extends UnsuccessfulResponseException {
  UnsuccessfulFuzzzyLawResponseException({
    super.message,
    super.uri,
    super.statusCode,
    super.errorCode,
    super.data,
  });
}
