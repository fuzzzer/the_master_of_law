part of 'laws_cubit.dart';

class LawsState {
  final StateStatus codesStatus;
  final StateStatus searchStatus;
  final StateStatus structureStatus;
  final StateStatus articleStatus;
  final List<dynamic> codes;
  final List<dynamic> searchResults;
  final String searchQuery;
  final Map<String, dynamic>? selectedCodeStructure;
  final Map<String, dynamic>? selectedArticle;
  final String? errorMessage;

  const LawsState({
    this.codesStatus = StateStatus.initial,
    this.searchStatus = StateStatus.initial,
    this.structureStatus = StateStatus.initial,
    this.articleStatus = StateStatus.initial,
    this.codes = const [],
    this.searchResults = const [],
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
    List<dynamic>? codes,
    List<dynamic>? searchResults,
    String? searchQuery,
    Map<String, dynamic>? selectedCodeStructure,
    Map<String, dynamic>? selectedArticle,
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
