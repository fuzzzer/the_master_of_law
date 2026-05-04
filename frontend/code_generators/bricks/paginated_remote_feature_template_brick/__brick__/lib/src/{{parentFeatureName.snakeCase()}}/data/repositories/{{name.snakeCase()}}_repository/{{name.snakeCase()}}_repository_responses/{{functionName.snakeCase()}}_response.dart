import 'package:themasteroflaw/src/src.dart';

sealed class {{functionName.pascalCase()}}Response {}

class {{functionName.pascalCase()}}Success extends {{functionName.pascalCase()}}Response {
  final Paginated{{itemModelName.pascalCase()}}List page;
  {{functionName.pascalCase()}}Success({required this.page});
}

class {{functionName.pascalCase()}}Failure extends {{functionName.pascalCase()}}Response {
  final {{functionName.pascalCase()}}FailureType failureType;
  {{functionName.pascalCase()}}Failure({required this.failureType});
}

enum {{functionName.pascalCase()}}FailureType {
  unknown;

  bool get isUnknown => this == unknown;
}
