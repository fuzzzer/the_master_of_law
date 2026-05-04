import 'package:bloc/bloc.dart';
import 'package:themasteroflaw/src/src.dart';

part '{{name.snakeCase()}}_state.dart';

class {{name.pascalCase()}}Cubit extends Cubit<{{name.pascalCase()}}State> {
  {{name.pascalCase()}}Cubit({
    required this.repository,
    //TODO change default page size if needed
    this.itemsPerPage = 20,
  }) : super(const {{name.pascalCase()}}State(status: StateStatus.initial));

  final {{name.pascalCase()}}Repository repository;
  final int itemsPerPage;
  int _currentPage = 1;

  Future<void> fetchFirstPage({{#hasQuery}}{{queryName.pascalCase()}}? query,{{/hasQuery}}) async {
    emit(const {{name.pascalCase()}}State(status: StateStatus.initial));
    _currentPage = 1;
    await _fetchPage(_currentPage, query: query);
  }

  Future<void> fetchNextPage() async {
    if (state.pageLimitReached || state.status.isLoading) return;
    _currentPage++;
    await _fetchPage(_currentPage, query: state.currentQuery);
  }

  Future<void> _fetchPage(
    int page, {
    {{#hasQuery}}{{queryName.pascalCase()}}? query,{{/hasQuery}}
  }) async {
    emit(state.copyWith(status: StateStatus.loading, currentQuery: query));

    final response = await repository.{{functionName.camelCase()}}(
      {{#hasQuery}}query: query ?? const {{queryName.pascalCase()}}(),{{/hasQuery}}
      itemsPerPage: itemsPerPage,
      currentPage: page,
    );

    final newState = switch (response) {
      {{functionName.pascalCase()}}Success() => state.copyWith(
          status: StateStatus.success,
          itemList: [
            if (state.itemList != null) ...state.itemList!,
            ...response.page.items,
          ],
          pageLimitReached: response.page.totalPagesCount == page,
        ),
      {{functionName.pascalCase()}}Failure() => state.copyWith(
          status: StateStatus.failed,
          failureType: response.failureType,
        ),
    };
    emit(newState);
  }
}
