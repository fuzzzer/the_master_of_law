import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:fuzzzy_law/src/src.dart';

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
        BlocProvider<CreditsCubit>(
          create: (_) => CreditsCubit(
            repository: CreditsRepository(
              remoteDataSource: CreditsRemoteDataSource(),
            ),
          )..load(),
        ),
      ],
      child: child,
    );
  }
}
