import 'package:themasteroflaw/src/src.dart';

class {{name.pascalCase()}}DataSource {
  final {{name.camelCase()}}BaseUrl = '${themasteroflawApiNetworkConfiguraion.themasteroflawBaseUri}/api/{{name.camelCase()}}';
  final themasteroflawHttpClient = sl.get<themasteroflawHttpClient>();

  Future<{{modelName.pascalCase()}}> {{functionName.camelCase()}}() async {
    final response = await themasteroflawHttpClient.post(
      Uri.parse('${{name.camelCase()}}BaseUrl/{{functionName.camelCase()}}'),
    );

    return parseWithExpectedDeserializationException<{{modelName.pascalCase()}}>(
      parser: () {
        //TODO add correct key to use from response
        final rawData = response.data['data'] as Map<String, dynamic>;
        return _parse{{modelName.pascalCase()}}(rawData);
      },
    );
  }

   {{modelName.pascalCase()}} _parse{{modelName.pascalCase()}}(Map<String, dynamic> map) {
    return {{modelName.pascalCase()}}(
      appSpecificParameter: 'TO CHANGE',
    );
  }


}
