import 'package:fuzzzy_law/src/src.dart';

class {{name.pascalCase()}}Repository {
  final {{name.pascalCase()}}DataSource dataSource;
  {{name.pascalCase()}}Repository({required this.dataSource});

  Future<{{functionName.pascalCase()}}Response> {{functionName.camelCase()}}({
    {{#hasQuery}}required {{queryName.pascalCase()}} query,{{/hasQuery}}
    required int itemsPerPage,
    required int currentPage,
  }) async {
    try {
      final page = await dataSource.{{functionName.camelCase()}}(
        {{#hasQuery}}query: query,{{/hasQuery}}
        itemsPerPage: itemsPerPage,
        currentPage: currentPage,
      );

      return {{functionName.pascalCase()}}Success(page: page);
    } catch (ex) {
      return {{functionName.pascalCase()}}Failure(failureType: {{functionName.pascalCase()}}FailureType.unknown);
    }
  }
}
