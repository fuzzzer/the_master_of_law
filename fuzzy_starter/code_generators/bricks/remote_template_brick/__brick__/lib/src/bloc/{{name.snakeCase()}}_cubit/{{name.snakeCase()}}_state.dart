part of '{{name.snakeCase()}}_cubit.dart';

class {{name.pascalCase()}}State {
  final StateStatus status;
  final {{modelName.pascalCase()}}? {{modelName.camelCase()}};
  final {{functionName.pascalCase()}}FailureType? failureType;

  const {{name.pascalCase()}}State({
    required this.status,
    this.{{modelName.camelCase()}},
    this.failureType,
  });

  {{name.pascalCase()}}State copyWith({
    StateStatus? status,
    {{modelName.pascalCase()}}? {{modelName.camelCase()}},
    {{functionName.pascalCase()}}FailureType? failureType,
  }) {
    return {{name.pascalCase()}}State(
      status: status ?? this.status,
      {{modelName.camelCase()}}: {{modelName.camelCase()}} ?? this.{{modelName.camelCase()}},
      failureType: failureType ?? this.failureType,
    );
  }

  @override
  String toString() => '{{name.pascalCase()}}State(status: $status, {{modelName.camelCase()}}: ${{modelName.camelCase()}}, failureType: $failureType)';
}
