import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

part 'laws_state.dart';

/// Manages laws browser state: codes list, search results, article viewing.
class LawsCubit extends Cubit<LawsState> {
  final LawsRepository _repository;

  LawsCubit({required LawsRepository repository})
      : _repository = repository,
        super(const LawsState());

  /// Load all legal codes.
  Future<void> loadCodes() async {
    emit(state.copyWith(codesStatus: StateStatus.loading));

    final result = await _repository.getCodes();
    switch (result) {
      case LawsSuccess<List<dynamic>>(:final data):
        emit(state.copyWith(
          codesStatus: StateStatus.success,
          codes: data,
        ));
      case LawsFailure<List<dynamic>>(:final message):
        emit(state.copyWith(
          codesStatus: StateStatus.failed,
          errorMessage: message,
        ));
    }
  }

  /// Search laws by query string.
  Future<void> searchLaws(String query) async {
    if (query.trim().isEmpty) {
      emit(state.copyWith(searchResults: [], searchQuery: ''));
      return;
    }

    emit(state.copyWith(searchStatus: StateStatus.loading, searchQuery: query));

    final result = await _repository.searchLaws(query);
    switch (result) {
      case LawsSuccess<List<dynamic>>(:final data):
        emit(state.copyWith(
          searchStatus: StateStatus.success,
          searchResults: data,
        ));
      case LawsFailure<List<dynamic>>(:final message):
        emit(state.copyWith(
          searchStatus: StateStatus.failed,
          errorMessage: message,
        ));
    }
  }

  /// Load a single code's structure (chapters + articles list).
  Future<void> loadCodeStructure(String codeId) async {
    emit(state.copyWith(structureStatus: StateStatus.loading));

    final result = await _repository.getCodeStructure(codeId);
    switch (result) {
      case LawsSuccess<Map<String, dynamic>>(:final data):
        emit(state.copyWith(
          structureStatus: StateStatus.success,
          selectedCodeStructure: data,
        ));
      case LawsFailure<Map<String, dynamic>>(:final message):
        emit(state.copyWith(
          structureStatus: StateStatus.failed,
          errorMessage: message,
        ));
    }
  }

  /// Load a single article's full text.
  Future<void> loadArticle(String articleId) async {
    emit(state.copyWith(articleStatus: StateStatus.loading));

    final result = await _repository.getArticle(articleId);
    switch (result) {
      case LawsSuccess<Map<String, dynamic>>(:final data):
        emit(state.copyWith(
          articleStatus: StateStatus.success,
          selectedArticle: data,
        ));
      case LawsFailure<Map<String, dynamic>>(:final message):
        emit(state.copyWith(
          articleStatus: StateStatus.failed,
          errorMessage: message,
        ));
    }
  }

  void clearSearch() {
    emit(state.copyWith(searchResults: [], searchQuery: ''));
  }
}
