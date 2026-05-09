import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:themasteroflaw/src/src.dart';

final navigatorKey = GlobalKey<NavigatorState>();

class AppRouter {
  static final GoRouter themasteroflawRouter = GoRouter(
    navigatorKey: navigatorKey,
    initialLocation: '/cases',
    observers: [NavigationLogger()],
    routes: <RouteBase>[
      StatefulShellRoute.indexedStack(
        builder: (context, state, navigationShell) {
          return MainShell(navigationShell: navigationShell);
        },
        branches: [
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/cases',
                builder: (context, state) => const MyCasesPage(),
                routes: [
                  GoRoute(
                    path: ':caseId',
                    builder: (context, state) {
                      final caseId = state.pathParameters['caseId']!;
                      return BlocProvider(
                        create: (_) => CaseDetailCubit(
                          repository: CaseRepository(localDataSource: CaseLocalDataSource()),
                        )..loadCase(caseId),
                        child: CaseWorkspacePage(caseId: caseId),
                      );
                    },
                  ),
                ],
              ),
            ],
          ),

          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/chat',
                builder: (context, state) => BlocProvider(
                  create: (_) => ConsultationCubit(
                    repository: ConsultationRepository(
                      remoteDataSource: ConsultationRemoteDataSource(),
                    ),
                    chatMode: ChatMode.lawsOnly,
                  ),
                  child: const ConsultationPage(),
                ),
              ),
            ],
          ),

          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/laws',
                builder: (context, state) => BlocProvider(
                  create: (_) => LawsCubit(
                    repository: LawsRepository(remoteDataSource: LawsRemoteDataSource()),
                  )..loadCodes(),
                  child: const LawsHomePage(),
                ),
              ),
            ],
          ),

          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/profile',
                builder: (context, state) => const ProfilePage(),
                routes: [
                  GoRoute(
                    path: 'dictionary',
                    builder: (context, state) => const LegalDictionaryPage(),
                  ),
                  GoRoute(
                    path: 'etiquette',
                    builder: (context, state) => const CourtEtiquettePage(),
                  ),
                  GoRoute(
                    path: 'contacts',
                    builder: (context, state) => const UsefulContactsPage(),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    ],
  );
}
