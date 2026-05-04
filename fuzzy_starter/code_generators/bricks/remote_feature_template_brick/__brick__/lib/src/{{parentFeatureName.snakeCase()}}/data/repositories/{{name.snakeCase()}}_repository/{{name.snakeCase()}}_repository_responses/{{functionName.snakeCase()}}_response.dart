import 'package:fuzzystarter/src/src.dart';

sealed class {{functionName.pascalCase()}}Response {}

class {{functionName.pascalCase()}}Success extends {{functionName.pascalCase()}}Response {
  final {{modelName.pascalCase()}} {{modelName.camelCase()}};

  {{functionName.pascalCase()}}Success({
    required this.{{modelName.camelCase()}},
  });
}

class {{functionName.pascalCase()}}Failure extends {{functionName.pascalCase()}}Response {
  final {{functionName.pascalCase()}}FailureType? failureType;

  {{functionName.pascalCase()}}Failure({
    this.failureType,
  });
}

enum {{functionName.pascalCase()}}FailureType {
  unknown;

  bool get isUnknown => this == unknown;
}
