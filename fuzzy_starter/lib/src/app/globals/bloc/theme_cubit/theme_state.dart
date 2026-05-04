part of 'theme_cubit.dart';

@immutable
class ThemeState {
  final ChosenBrightness chosenBrightness;

  const ThemeState({
    required this.chosenBrightness,
  });

  ThemeState copyWith({
    ChosenBrightness? chosenBrightness,
  }) {
    return ThemeState(
      chosenBrightness: chosenBrightness ?? this.chosenBrightness,
    );
  }
}

Brightness getBrightnessFromChosenBrightness(ChosenBrightness brightness) {
  return brightness.isSystem
      ? WidgetsBinding.instance.platformDispatcher.platformBrightness.isLight
          ? Brightness.light
          : Brightness.dark
      : brightness.isLight
          ? Brightness.light
          : Brightness.dark;
}

class ThemeStateBuilder extends StatelessWidget {
  const ThemeStateBuilder({
    super.key,
    required this.builder,
  });

  final Widget Function(Brightness brightness) builder;

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ThemeCubit, ThemeState>(
      builder: (context, state) {
        final brightness = getBrightnessFromChosenBrightness(state.chosenBrightness);

        return builder(brightness);
      },
    );
  }
}
