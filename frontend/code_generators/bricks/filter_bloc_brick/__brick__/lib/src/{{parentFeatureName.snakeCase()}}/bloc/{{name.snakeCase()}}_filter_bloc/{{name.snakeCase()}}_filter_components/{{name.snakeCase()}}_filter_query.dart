import 'package:themasteroflaw/src/src.dart';

class {{name.pascalCase()}}FilterQuery {
  final String? searchText;
  // TODO: Add your own fields, e.g. final CategoryData category;
  // final CategoryData appliedCategoryFilter;
  // final double? minPrice, maxPrice;
  // final SortType sortBy;

  const {{name.pascalCase()}}FilterQuery({
    this.searchText,
    // TODO: init other fields with defaults
  });

  const {{name.pascalCase()}}FilterQuery.empty() : searchText = null;

  {{name.pascalCase()}}FilterQuery copyWith({
    String? searchText,
  }) {
    return {{name.pascalCase()}}FilterQuery(
      searchText: searchText ?? this.searchText,
    );
  }
}
