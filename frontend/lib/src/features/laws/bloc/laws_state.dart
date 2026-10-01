part of 'laws_cubit.dart';

class LawsState {
  final StateStatus codesStatus;
  final StateStatus searchStatus;
  final StateStatus structureStatus;
  final StateStatus articleStatus;
  final List<LawCode> codes;
  final LawSearchResults? searchResults;
  final String searchQuery;
  final Map<String, dynamic>? selectedCodeStructure;
  final LawArticleDetail? selectedArticle;
  final String? errorMessage;

  const LawsState({
    this.codesStatus = StateStatus.initial,
    this.searchStatus = StateStatus.initial,
    this.structureStatus = StateStatus.initial,
    this.articleStatus = StateStatus.initial,
    this.codes = const [],
    this.searchResults,
    this.searchQuery = '',
    this.selectedCodeStructure,
    this.selectedArticle,
    this.errorMessage,
  });

  LawsState copyWith({
    StateStatus? codesStatus,
    StateStatus? searchStatus,
    StateStatus? structureStatus,
    StateStatus? articleStatus,
    List<LawCode>? codes,
    LawSearchResults? searchResults,
    String? searchQuery,
    Map<String, dynamic>? selectedCodeStructure,
    LawArticleDetail? selectedArticle,
    String? errorMessage,
  }) {
    return LawsState(
      codesStatus: codesStatus ?? this.codesStatus,
      searchStatus: searchStatus ?? this.searchStatus,
      structureStatus: structureStatus ?? this.structureStatus,
      articleStatus: articleStatus ?? this.articleStatus,
      codes: codes ?? this.codes,
      searchResults: searchResults ?? this.searchResults,
      searchQuery: searchQuery ?? this.searchQuery,
      selectedCodeStructure: selectedCodeStructure ?? this.selectedCodeStructure,
      selectedArticle: selectedArticle ?? this.selectedArticle,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}
