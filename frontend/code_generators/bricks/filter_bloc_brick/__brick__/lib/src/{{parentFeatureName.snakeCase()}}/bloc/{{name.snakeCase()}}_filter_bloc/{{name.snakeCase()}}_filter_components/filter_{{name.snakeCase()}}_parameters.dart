import 'package:themasteroflaw/src/src.dart';

/// Object passed to `compute()` so that the heavy filtering work
/// runs in a background isolate.  Must be **top-level / const**.
class Filter{{name.pascalCase()}}Parameters {
  final List<{{filterable_model.pascalCase()}}> allItems;
  final {{name.pascalCase()}}FilterQuery query;

  const Filter{{name.pascalCase()}}Parameters({
    required this.allItems,
    required this.query,
  });
}
