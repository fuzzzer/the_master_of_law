import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:themasteroflaw/src/src.dart';

class GlobalBlocProviders extends StatelessWidget {
  const GlobalBlocProviders({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider<ThemeCubit>(
          create: (_) => ThemeCubit(),
        ),
        BlocProvider<LocalizationCubit>(
          create: (_) => LocalizationCubit(),
        ),
        BlocProvider<CasesCubit>(
          create: (_) => CasesCubit(
            repository: CaseRepository(localDataSource: CaseLocalDataSource()),
          )..loadCases(),
        ),
      ],
      child: child,
    );
  }
}
