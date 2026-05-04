part of '{{name.snakeCase()}}_cubit.dart';

class {{name.pascalCase()}}State {
  final StateStatus status;
  final List<{{itemModelName.pascalCase()}}>? itemList;
  final {{functionName.pascalCase()}}FailureType? failureType;
  final bool pageLimitReached;
  {{#hasQuery}}final {{queryName.pascalCase()}}? currentQuery;{{/hasQuery}}

  const {{name.pascalCase()}}State({
    required this.status,
    this.itemList,
    this.failureType,
    this.pageLimitReached = false,
    {{#hasQuery}}this.currentQuery,{{/hasQuery}}
  });

  {{name.pascalCase()}}State copyWith({
    StateStatus? status,
    List<{{itemModelName.pascalCase()}}> ? itemList,
    {{functionName.pascalCase()}}FailureType? failureType,
    bool? pageLimitReached,
    {{#hasQuery}}{{queryName.pascalCase()}}? currentQuery,{{/hasQuery}}
  }) {
    return {{name.pascalCase()}}State(
      status: status ?? this.status,
      itemList: itemList ?? this.itemList,
      failureType: failureType ?? this.failureType,
      pageLimitReached: pageLimitReached ?? this.pageLimitReached,
      {{#hasQuery}}currentQuery: currentQuery ?? this.currentQuery,{{/hasQuery}}
    );
  }

  @override
  String toString() =>
      '{{name.pascalCase()}}State(status: $status, items: $itemList, failureType: $failureType, pageLimitReached: $pageLimitReached{{#hasQuery}}, currentQuery: $currentQuery{{/hasQuery}})';
}
