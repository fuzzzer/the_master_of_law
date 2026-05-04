import 'package:bloc/bloc.dart';
import 'package:themasteroflaw/src/src.dart';

export '{{name.snakeCase()}}_cubit.dart';

part '{{name.snakeCase()}}_state.dart';

class {{name.pascalCase()}}Cubit extends Cubit<{{name.pascalCase()}}State> {
  {{name.pascalCase()}}Cubit({required this.{{name.camelCase()}}Repository}) : super(const {{name.pascalCase()}}State(status: StateStatus.initial));

  final {{name.pascalCase()}}Repository {{name.camelCase()}}Repository;

  Future<void> {{functionName.camelCase()}}() async {
    emit(state.copyWith(status: StateStatus.loading));

    final {{functionName.camelCase()}}Response = await {{name.camelCase()}}Repository.{{functionName.camelCase()}}();

    final newState = switch ({{functionName.camelCase()}}Response) {
      {{functionName.pascalCase()}}Success() => state.copyWith(
          status: StateStatus.success,
          {{modelName.camelCase()}}: {{functionName.camelCase()}}Response.{{modelName.camelCase()}},
        ),
      {{functionName.pascalCase()}}Failure() => state.copyWith(
          status: StateStatus.failed,
          failureType: {{functionName.camelCase()}}Response.failureType,
        ),
    };

    emit(newState);
  }
}
