part of '{{name.snakeCase()}}_filter_bloc.dart';

sealed class {{name.pascalCase()}}FilterEvent {}

class {{name.pascalCase()}}StartFiltering extends {{name.pascalCase()}}FilterEvent {
  final {{name.pascalCase()}}FilterQuery query;
  {{name.pascalCase()}}StartFiltering({required this.query});

  {{name.pascalCase()}}StartFiltering.empty()
      : query = const {{name.pascalCase()}}FilterQuery.empty();
}
