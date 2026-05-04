class DropdownItem<T> {
  final String label;
  final T valueId;

  const DropdownItem({
    required this.label,
    required this.valueId,
  });

  @override
  bool operator ==(covariant DropdownItem other) {
    if (identical(this, other)) return true;

    return other.label == label && other.valueId == valueId;
  }

  @override
  int get hashCode => label.hashCode ^ valueId.hashCode;
}
