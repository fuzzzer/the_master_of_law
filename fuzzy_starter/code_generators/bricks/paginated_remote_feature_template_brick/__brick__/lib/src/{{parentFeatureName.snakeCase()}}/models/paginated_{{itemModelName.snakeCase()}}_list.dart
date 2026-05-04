import '{{itemModelName.snakeCase()}}.dart';

class Paginated{{itemModelName.pascalCase()}}List {
  final List<{{itemModelName.pascalCase()}}> items;
  final int totalPagesCount;

  Paginated{{itemModelName.pascalCase()}}List({
    required this.items,
    required this.totalPagesCount,
  });

  @override
  String toString() =>
      'Paginated{{itemModelName.pascalCase()}}List(totalPagesCount: $totalPagesCount, items: $items)';
}
