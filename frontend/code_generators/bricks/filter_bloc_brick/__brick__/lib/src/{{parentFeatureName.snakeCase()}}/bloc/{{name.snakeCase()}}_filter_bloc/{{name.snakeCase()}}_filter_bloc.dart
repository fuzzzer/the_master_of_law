// ignore_for_file: public_member_api_docs, sort_constructors_first
import 'dart:async';
import 'package:bloc/bloc.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:flutter/foundation.dart';

part '{{name.snakeCase()}}_filter_event.dart';
part '{{name.snakeCase()}}_filter_state.dart';

class {{name.pascalCase()}}FilterBloc
    extends Bloc<{{name.pascalCase()}}FilterEvent, {{name.pascalCase()}}FilterState> {
  /// All items that can be filtered.
  final List<{{filterable_model.pascalCase()}}> allItems;                         

  {{name.pascalCase()}}FilterBloc({required this.allItems})
      : super(
          const {{name.pascalCase()}}FilterState(
            status: {{name.pascalCase()}}FilterStatus.initial,
            lastQuery: {{name.pascalCase()}}FilterQuery.empty(),
          ),
        ) {
    on<{{name.pascalCase()}}StartFiltering>(_onStartFiltering);
  }

  FutureOr<void> _onStartFiltering(
    {{name.pascalCase()}}StartFiltering event,
    Emitter<{{name.pascalCase()}}FilterState> emit,
  ) async {
    emit(state.copyWith(status: {{name.pascalCase()}}FilterStatus.loading));

    final query = event.query;

    if (_isInitialQuery(query)) {
      emit(state.copyWith(
        status: {{name.pascalCase()}}FilterStatus.initial,
        lastQuery: query,
      ));
      return;
    }

  //NOTE: computing evering on isolate, so we dont interfire with ui builds
    final filtered = await compute(
      _intermediateFilterItems,
      Filter{{name.pascalCase()}}Parameters(
        allItems: allItems,
        query: query,
      ),
    );

    _sortItems(filtered, query);

    emit(state.copyWith(
      status: {{name.pascalCase()}}FilterStatus.filtered,
      filtered: filtered,
      lastQuery: query,
    ));
  }

  /* ---------------------------------------------------------------- *\
                  filter entry point to be used with isolate 
  \* ---------------------------------------------------------------- */

  static List<{{filterable_model.pascalCase()}}> _intermediateFilterItems(
    Filter{{name.pascalCase()}}Parameters parameters,
  ) {
    return _filterItems(parameters.allItems, parameters.query);
  }

  /* ---------------------------------------------------------------- *\
             individual filer methods for cleaner filtering
  \* ---------------------------------------------------------------- */

  bool _isInitialQuery({{name.pascalCase()}}FilterQuery query) =>
      query == const {{name.pascalCase()}}FilterQuery.empty();

  //NOTE: general method that calls all the filering methods one by one
  static List<{{filterable_model.pascalCase()}}> _filterItems(
    List<{{filterable_model.pascalCase()}}> items,
    {{name.pascalCase()}}FilterQuery query,
  ) {
    return items.where((item) {
      return _matchesSearch(item, query.searchText);
      // && … add more predicates here
    }).toList(growable: false);
  }

  static bool _matchesSearch({{filterable_model.pascalCase()}} item, String? search) {
    if (search == null || search.trim().isEmpty) return true;
    final words = search.toLowerCase().split(' ');
    // TODO customise per-domain
    return item.label?.toLowerCase().contains(words.first) ?? false;
  }

  void _sortItems(List<{{filterable_model.pascalCase()}}> items, {{name.pascalCase()}}FilterQuery query) {
    // TODO implement sort logic
  }
}
