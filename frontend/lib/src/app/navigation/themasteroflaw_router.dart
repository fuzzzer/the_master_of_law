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
          // ── Tab 0: Cases ────────────────────────────────────
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/cases',
                builder: (context, state) => BlocProvider(
                  create: (_) => CasesCubit(
                    repository: CaseRepository(localDataSource: CaseLocalDataSource()),
                  )..loadCases(),
                  child: const MyCasesPage(),
                ),
                routes: [
                  GoRoute(
                    path: ':caseId',
                    builder: (context, state) {
                      final caseId = state.pathParameters['caseId']!;
                      return MultiBlocProvider(
                        providers: [
                          BlocProvider(
                            create: (_) => CaseDetailCubit(
                              repository: CaseRepository(localDataSource: CaseLocalDataSource()),
                            )..loadCase(caseId),
                          ),
                          BlocProvider(
                            create: (_) => CasesCubit(
                              repository: CaseRepository(localDataSource: CaseLocalDataSource()),
                            ),
                          ),
                        ],
                        child: CaseWorkspacePage(caseId: caseId),
                      );
                    },
                  ),
                ],
              ),
            ],
          ),

          // ── Tab 1: Chat (AI Consultation) ────────────────────
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

          // ── Tab 2: Laws ─────────────────────────────────────
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

          // ── Tab 3: Profile ──────────────────────────────────
          StatefulShellBranch(
            routes: [
              GoRoute(
                path: '/profile',
                builder: (context, state) => const ProfilePage(),
              ),
            ],
          ),
        ],
      ),
    ],
  );
}
