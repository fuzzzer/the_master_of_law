part of 'localization_cubit.dart';

@immutable
class LocalizationState {
  final Locale locale;

  const LocalizationState({
    required this.locale,
  });

  LocalizationState copyWith({
    Locale? locale,
  }) {
    return LocalizationState(
      locale: locale ?? this.locale,
    );
  }

  @override
  String toString() => 'LocalizationState(locale: $locale)';

  @override
  bool operator ==(covariant LocalizationState other) {
    if (identical(this, other)) return true;

    return other.locale == locale;
  }

  @override
  int get hashCode => locale.hashCode;
}

class LocalizationStateBuilder extends StatelessWidget {
  const LocalizationStateBuilder({
    super.key,
    required this.builder,
  });

  final Widget Function(Locale locale) builder;

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<LocalizationCubit, LocalizationState>(
      builder: (context, state) {
        return builder(state.locale);
      },
    );
  }
}
