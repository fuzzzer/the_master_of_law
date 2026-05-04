import 'package:themasteroflaw/src/src.dart';

class {{name.pascalCase()}}DataSource {
  final http = sl.get<themasteroflawHttpClient>();
  final baseUrl =
      '${themasteroflawApiNetworkConfiguration.themasteroflawBaseUri}/api/{{name.camelCase()}}';

  Future<Paginated{{itemModelName.pascalCase()}}List> {{functionName.camelCase()}}({
    {{#hasQuery}}required {{queryName.pascalCase()}} query,{{/hasQuery}}
    required int itemsPerPage,
    required int currentPage,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/{{functionName.camelCase()}}'),
      body: {
        'itemsPerPage': itemsPerPage,
        'currentPage': currentPage,
        {{#hasQuery}}
        if (query.searchText != null) 'searchText': query.searchText!,
        {{/hasQuery}}
      },
    );

    return parseWithExpectedDeserializationException<
        Paginated{{itemModelName.pascalCase()}}List>(
      parser: () {
        final data = response.data['data'] as Map<String, dynamic>;

        final items = (data['items'] as List)
            .map((e) =>
                _parse{{itemModelName.pascalCase()}}(e as Map<String, dynamic>))
            .toList();

        return Paginated{{itemModelName.pascalCase()}}List(
          items: items,
          totalPagesCount: data['totalPagesCount'] as int,
        );
      },
    );
  }

  {{itemModelName.pascalCase()}} _parse{{itemModelName.pascalCase()}}(
    Map<String, dynamic> json,
  ) {
    // TODO(map real fields)
    return const {{itemModelName.pascalCase()}}();
  }
}
