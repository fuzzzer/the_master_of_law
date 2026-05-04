import 'package:themasteroflaw/src/src.dart';

class {{name.pascalCase()}}Repository {
  final {{name.pascalCase()}}DataSource {{name.camelCase()}}DataSource;

  {{name.pascalCase()}}Repository({
    required this.{{name.camelCase()}}DataSource,
  });

  Future<{{functionName.pascalCase()}}Response> {{functionName.camelCase()}}() async {
    try {
      final {{modelName.camelCase()}} = await {{name.camelCase()}}DataSource.{{functionName.camelCase()}}();

      return {{functionName.pascalCase()}}Success(
        {{modelName.camelCase()}}: {{modelName.camelCase()}},
      );
    } catch (ex) {
      return {{functionName.pascalCase()}}Failure();
    }
  }
}
