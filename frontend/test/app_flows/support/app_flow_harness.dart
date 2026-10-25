import 'dart:async';
import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_law/src/src.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:hive/hive.dart';
import 'package:package_info_plus/package_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'fake_law_server.dart';

const apiKeyStorageKey = 'temporary_api_key';

/// Secure storage kept in memory: no platform channel, nothing left behind.
class InMemorySecureStorage extends SecureStorageService {
  InMemorySecureStorage() : super(const FlutterSecureStorage());

  final Map<String, String> store = {};

  @override
  Future<String?> getData(String key) async => store[key];

  @override
  Future<void> saveData(String key, String value) async => store[key] = value;

  @override
  Future<void> deleteData(String key) async => store.remove(key);

  @override
  Future<void> clearAllSecureData() async => store.clear();
}

/// The app's dependency injection with every outside edge replaced: the
/// backend by [FakeLawServer], secure storage by memory, cases by an
/// in-memory Hive box. Everything between those edges is the real app.
class AppFlowHarness {
  AppFlowHarness._(this.server, this.storage);

  final FakeLawServer server;
  final InMemorySecureStorage storage;

  static bool _hiveReady = false;

  static Future<AppFlowHarness> start({String? storedKey}) async {
    GoogleFonts.config.allowRuntimeFetching = false;
    SharedPreferences.setMockInitialValues({});
    dotenv.testLoad(
      fileInput:
          'API_BASE_URL=${FakeLawServer.baseUrl}\n'
          'BASE_URI=${FakeLawServer.baseUrl}',
    );
    await _openCasesBox();

    final harness = AppFlowHarness._(FakeLawServer(), InMemorySecureStorage());
    if (storedKey != null) {
      await harness.storage.saveData(apiKeyStorageKey, storedKey);
    }
    await harness._registerDependencies();
    AppRouter.fuzzzyLawRouter.go('/auth');
    return harness;
  }

  Future<String?> get storedKey => storage.getData(apiKeyStorageKey);

  Future<void> _registerDependencies() async {
    final packageInfo = FakeLawData.packageInfo;
    final models = ModelPreferenceService(storage);
    await models.load();

    _replace<PackageInfo>(packageInfo);
    _replace<SecureStorageService>(storage);
    _replace<DeviceIdService>(DeviceIdService(storage));
    _replace<ModelPreferenceService>(models);
    _replace<ChatTurnRegistry>(ChatTurnRegistry());
    _replace<FuzzzyLawHttpClient>(
      FakeServerHttpClient(server: server, packageInfo: packageInfo),
    );
  }

  static void _replace<T extends Object>(T instance) {
    if (sl.isRegistered<T>(instance: instance)) sl.unregister<T>();
    sl.registerSingleton<T>(instance);
  }

  /// An in-memory `cases` box, opened before the app asks for it, so
  /// `CaseLocalDataSource` finds it already open and never touches disk.
  static Future<void> _openCasesBox() async {
    if (!_hiveReady) {
      Hive
        ..registerAdapter(CaseDataAdapter())
        ..registerAdapter(FactDataAdapter())
        ..registerAdapter(ArgumentDataAdapter())
        ..registerAdapter(EvidenceDataAdapter())
        ..registerAdapter(StrategyDataAdapter())
        ..registerAdapter(TimelineEventDataAdapter())
        ..registerAdapter(RiskDataAdapter())
        ..registerAdapter(ActionItemDataAdapter())
        ..registerAdapter(LinkedArticleDataAdapter())
        ..registerAdapter(ClarificationDataAdapter());
      _hiveReady = true;
    }
    if (Hive.isBoxOpen('cases')) {
      await Hive.box<CaseData>('cases').clear();
    } else {
      await Hive.openBox<CaseData>('cases', bytes: Uint8List(0));
    }
  }
}

/// The app's real router, global providers and theme. Left out on purpose:
/// the developer overlays (admin head, shake-to-open panel), which need
/// sensors and a live admin endpoint.
Future<void> pumpFuzzzyLawApp(WidgetTester tester) async {
  _usePhoneViewport(tester);
  await tester.pumpWidget(
    GlobalBlocProviders(
      child: MaterialApp.router(
        routerConfig: AppRouter.fuzzzyLawRouter,
        theme: buildQuietTheme(),
        locale: const Locale('ka'),
        localizationsDelegates: FuzzzyLawLocalizations.localizationsDelegates,
        supportedLocales: FuzzzyLawLocalizations.supportedLocales,
      ),
    ),
  );
}

/// One real screen under the app's global providers and theme, for a flow
/// whose route cannot take a fake (the chat socket).
Future<void> pumpScreen(WidgetTester tester, Widget screen) async {
  _usePhoneViewport(tester);
  await tester.pumpWidget(
    GlobalBlocProviders(
      child: MaterialApp(
        theme: buildQuietTheme(),
        locale: const Locale('ka'),
        localizationsDelegates: FuzzzyLawLocalizations.localizationsDelegates,
        supportedLocales: FuzzzyLawLocalizations.supportedLocales,
        home: screen,
      ),
    ),
  );
}

/// A 360 x 780 dp phone, the width the app's layout checks are made at.
void _usePhoneViewport(WidgetTester tester) {
  tester.view
    ..devicePixelRatio = 3
    ..physicalSize = const Size(1080, 2340);
  addTearDown(tester.view.reset);
}

/// The chat screen exactly as the `/chat` route builds it, but on a
/// scripted socket.
Widget chatScreen(ScriptedChatRemoteDataSource dataSource) => BlocProvider(
  create: (_) => ConsultationCubit(
    repository: ConsultationRepository(remoteDataSource: dataSource),
    turns: sl.get<ChatTurnRegistry>(),
    chatMode: ChatMode.lawsOnly,
  ),
  child: const ConsultationPage(),
);

/// The app theme without the font download noise: with runtime fetching off,
/// GoogleFonts reports each missing family asynchronously. Those reports are
/// the only thing swallowed here (same reasoning as `theme_roles_test.dart`).
ThemeData buildQuietTheme() {
  late ThemeData theme;
  runZonedGuarded(() => theme = FuzzzyLawTheme.dark(), (error, stack) {
    final text = error.toString();
    final isFontNoise =
        text.contains('allowRuntimeFetching') ||
        text.contains('Failed to load font');
    if (!isFontNoise) Zone.root.handleUncaughtError(error, stack);
  });
  return theme;
}

/// Pumps frames until [finder] matches, or fails after [timeout].
///
/// Not `pumpAndSettle`: the chat's typing dots and the loading rings repeat
/// forever, so "settled" never comes on those screens.
Future<void> pumpUntilFound(
  WidgetTester tester,
  Finder finder, {
  Duration timeout = const Duration(seconds: 10),
}) async {
  const step = Duration(milliseconds: 100);
  for (var waited = Duration.zero; waited < timeout; waited += step) {
    await tester.pump(step);
    if (finder.evaluate().isNotEmpty) return;
  }
  final onScreen = find
      .byType(Text)
      .evaluate()
      .map((e) => (e.widget as Text).data ?? '')
      .where((t) => t.isNotEmpty);
  fail(
    'Not found within ${timeout.inSeconds}s: $finder\n'
    'Texts on screen: ${onScreen.join(' | ')}',
  );
}

/// Scrolls [finder] into view, as a reader would, then taps it.
Future<void> scrollToAndTap(WidgetTester tester, Finder finder) async {
  if (finder.evaluate().isEmpty) {
    await tester.scrollUntilVisible(
      finder,
      200,
      scrollable: find.byType(Scrollable).hitTestable().first,
    );
  }
  await tester.ensureVisible(finder);
  // Lets a sheet or page that is still sliding in reach its resting place.
  await tester.pump(const Duration(milliseconds: 500));
  await tester.tap(finder);
}

/// One reader journey: a widget test that always ends with [finishFlow].
void appFlow(
  String description,
  Future<void> Function(WidgetTester tester) body, {
  bool skip = false,
}) {
  testWidgets(description, (tester) async {
    await body(tester);
    await finishFlow(tester);
  }, skip: skip);
}

/// Ends a flow the way the next one expects to start: requests finished,
/// no key, the router back on the key screen, the tree gone.
///
/// The router is the app's single static instance, so a shell left mounted
/// at the end of one flow would collide with the next flow's shell.
Future<void> finishFlow(WidgetTester tester) async {
  await tester.pump(const Duration(seconds: 1));
  await sl.get<SecureStorageService>().deleteData(apiKeyStorageKey);
  AppRouter.fuzzzyLawRouter.go('/auth');
  await tester.pump(const Duration(seconds: 1));
  await tester.pumpWidget(const SizedBox.shrink());
  await tester.pump(const Duration(seconds: 1));
}
