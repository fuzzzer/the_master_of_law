import 'package:themasteroflaw/src/src.dart';

class {{name.pascalCase()}}DataSource {
  final {{name.camelCase()}}BaseUrl = '${themasteroflawApiNetworkConfiguration.themasteroflawBaseUri}/api/{{name.camelCase()}}';
  final themasteroflawHttpClient = sl.get<themasteroflawHttpClient>();

  Future<{{modelName.pascalCase()}}> {{functionName.camelCase()}}({{#hasRequestData}}{
      required {{requestDataName.pascalCase()}} {{requestDataName.camelCase()}},
    }{{/hasRequestData}}) async {
    final response = await themasteroflawHttpClient.post(
      Uri.parse('${{name.camelCase()}}BaseUrl/{{functionName.camelCase()}}'),
      {{#hasRequestData}}body: _turn{{requestDataName.pascalCase()}}ToBody({{requestDataName.camelCase()}}),{{/hasRequestData}}
    );

    return parseWithExpectedDeserializationException<{{modelName.pascalCase()}}>(
      parser: () {
        final rawData = response.data['data'] as Map<String, dynamic>;
        return _parse{{modelName.pascalCase()}}(rawData);
      },
    );
  }

  {{#hasRequestData}}
  Map<String, dynamic> _turn{{requestDataName.pascalCase()}}ToBody({{requestDataName.pascalCase()}} data) {
    return {
      //TODO Add necessary fields
      'toChange': data.toChange,
    };
  }
  {{/hasRequestData}}

   {{modelName.pascalCase()}} _parse{{modelName.pascalCase()}}(Map<String, dynamic> map) {
    return {{modelName.pascalCase()}}(
      appSpecificParameter: 'TO CHANGE',
    );
  }


}
