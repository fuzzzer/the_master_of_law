enum {{name.pascalCase()}}FilterStatus {
  initial,
  loading,
  filtered;

  bool get isInitial => this == {{name.pascalCase()}}FilterStatus.initial;
  bool get isLoading => this == {{name.pascalCase()}}FilterStatus.loading;
  bool get isFiltered => this == {{name.pascalCase()}}FilterStatus.filtered;
}
