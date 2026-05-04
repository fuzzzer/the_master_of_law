part of '{{name.snakeCase()}}_filter_bloc.dart';

enum {{name.pascalCase()}}FilterStatus { initial, loading, filtered }

extension _StatusX on {{name.pascalCase()}}FilterStatus {
  bool get isInitial => this == {{name.pascalCase()}}FilterStatus.initial;
  bool get isLoading => this == {{name.pascalCase()}}FilterStatus.loading;
  bool get isFiltered => this == {{name.pascalCase()}}FilterStatus.filtered;
}

class {{name.pascalCase()}}FilterState {
  final {{name.pascalCase()}}FilterStatus status;
  final List<{{filterable_model.pascalCase()}}>? filtered;
  final {{name.pascalCase()}}FilterQuery lastQuery;

  const {{name.pascalCase()}}FilterState({
    required this.status,
    this.filtered,
    required this.lastQuery,
  });

  bool get nothingFound => filtered != null && filtered!.isEmpty;

  {{name.pascalCase()}}FilterState copyWith({
    {{name.pascalCase()}}FilterStatus? status,
    List<{{filterable_model.pascalCase()}}>? filtered,
    {{name.pascalCase()}}FilterQuery? lastQuery,
  }) {
    return {{name.pascalCase()}}FilterState(
      status: status ?? this.status,
      filtered: filtered ?? this.filtered,
      lastQuery: lastQuery ?? this.lastQuery,
    );
  }
}
