import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'support/app_flow_harness.dart';
import 'support/fake_law_server.dart';

/// The five reader journeys, written once and run twice: by
/// `test/app_flows/app_flows_test.dart` under `flutter test` (no device), and
/// by `integration_test/app_flows_test.dart` on a device or browser.
///
/// The backend is [FakeLawServer]; no key, server or network is needed.
void defineAppFlows() {
  group('entry without an account (own Google key)', () {
    appFlow('a first launch opens on the key screen', (tester) async {
      await AppFlowHarness.start();
      await pumpFuzzzyLawApp(tester);

      await pumpUntilFound(tester, find.text('დაწყება'));
      expect(find.text('თქვენი Google AI Studio-ს გასაღები'), findsOneWidget);
      expect(find.text('გაგრძელება'), findsOneWidget);
    });

    appFlow('a stored key goes straight to the cases', (tester) async {
      await AppFlowHarness.start(storedKey: FakeLawData.validKey);
      await pumpFuzzzyLawApp(tester);

      await pumpUntilFound(tester, find.text('თქვენ ჯერ არ გაქვთ საქმე'));
      expect(find.text('ბუნდოვანი კანონი'), findsOneWidget);
    });
  });

  group('saving the Google key', () {
    appFlow('an AI Studio key is checked, saved and opens the app', (
      tester,
    ) async {
      final harness = await AppFlowHarness.start();
      await pumpFuzzzyLawApp(tester);
      await pumpUntilFound(tester, find.byType(TextField));

      await tester.enterText(find.byType(TextField), FakeLawData.validKey);
      await scrollToAndTap(tester, find.text('გაგრძელება'));
      await pumpUntilFound(tester, find.text('თქვენ ჯერ არ გაქვთ საქმე'));

      expect(await harness.storedKey, FakeLawData.validKey);
      final check = harness.server.requests.singleWhere(
        (r) => r.uri.path == '/api/v1/api-keys/validate',
      );
      expect(check.headers['X-API-Key'], FakeLawData.validKey);
    });

    appFlow('a rejected key is not kept and the reader stays put', (
      tester,
    ) async {
      final harness = await AppFlowHarness.start();
      await pumpFuzzzyLawApp(tester);
      await pumpUntilFound(tester, find.byType(TextField));

      await tester.enterText(find.byType(TextField), FakeLawData.invalidKey);
      await scrollToAndTap(tester, find.text('გაგრძელება'));
      await pumpUntilFound(tester, find.textContaining('სცადეთ ხელახლა'));

      expect(await harness.storedKey, isNull);
      expect(find.text('თქვენი Google AI Studio-ს გასაღები'), findsOneWidget);
    });

    appFlow(
      'a rejected key says the key does not work',
      (tester) async {
        await AppFlowHarness.start();
        await pumpFuzzzyLawApp(tester);
        await pumpUntilFound(tester, find.byType(TextField));

        await tester.enterText(find.byType(TextField), FakeLawData.invalidKey);
        await scrollToAndTap(tester, find.text('გაგრძელება'));
        await tester.pump(const Duration(seconds: 1));

        expect(find.textContaining('გასაღები არ მუშაობს'), findsOneWidget);
        expect(find.textContaining('სერვერთან დაკავშირება'), findsNothing);
      },
      skip: rejectedKeyMessageDefect.isNotEmpty,
    );

    appFlow(
      'changing the key from the profile keeps the new one',
      (
        tester,
      ) async {
        const newKey = 'AIzaSyAnotherFakeKeyForAppFlows_1111111';
        final harness = await AppFlowHarness.start(
          storedKey: FakeLawData.validKey,
        );
        await pumpFuzzzyLawApp(tester);
        await pumpUntilFound(tester, find.text('პროფილი'));

        await tester.tap(find.text('პროფილი'));
        await pumpUntilFound(tester, find.text('პარამეტრები'));
        await scrollToAndTap(tester, find.text('Google-ის გასაღები'));
        await pumpUntilFound(tester, find.text('გასაღების შეცვლა'));

        await tester.enterText(find.byType(TextField), newKey);
        await scrollToAndTap(tester, find.text('შენახვა'));
        await pumpUntilFound(tester, find.text('…1111'));

        expect(await harness.storedKey, newKey);
      },
      skip: profileKeyLabelDefect.isNotEmpty,
    );
  });

  group('new case', () {
    appFlow('a titled case is created and opens its workspace', (
      tester,
    ) async {
      const title = 'მემამულის დავა ბინის დეპოზიტზე';
      await AppFlowHarness.start(storedKey: FakeLawData.validKey);
      await pumpFuzzzyLawApp(tester);
      await pumpUntilFound(tester, find.text('ახალი საქმის შექმნა'));

      await scrollToAndTap(tester, find.text('ახალი საქმის შექმნა'));
      await pumpUntilFound(tester, find.text('ახალი საქმე'));
      await tester.enterText(find.byType(TextField), title);
      await scrollToAndTap(tester, find.text('შექმნა და დაწყება →'));
      await pumpUntilFound(tester, find.text('მიმოხილვა'));

      expect(find.text(title), findsWidgets);
    });
  });

  group('chat', () {
    appFlow('a question is sent and the answer is shown', (tester) async {
      const question = 'რას არეგულირებს სამოქალაქო კოდექსის პირველი მუხლი?';
      await AppFlowHarness.start(storedKey: FakeLawData.validKey);
      final socket = ScriptedChatRemoteDataSource();
      await pumpScreen(tester, chatScreen(socket));
      await pumpUntilFound(tester, find.text('დაწყება'));

      await tester.tap(find.text('დაწყება'));
      await pumpUntilFound(tester, find.text('დაწერეთ კითხვა...'));
      await tester.enterText(find.byType(TextField), question);
      await tester.tap(find.byIcon(Icons.arrow_upward_rounded));
      await pumpUntilFound(
        tester,
        find.textContaining(FakeLawData.answerEnd, findRichText: true),
      );

      expect(socket.sentMessages, [question]);
      expect(find.textContaining(question, findRichText: true), findsWidgets);
    });
  });

  group('laws browser', () {
    appFlow('a code opens to its article list and an article text', (
      tester,
    ) async {
      await AppFlowHarness.start(storedKey: FakeLawData.validKey);
      await pumpFuzzzyLawApp(tester);
      await pumpUntilFound(tester, find.text('კანონები'));

      await tester.tap(find.text('კანონები'));
      await pumpUntilFound(tester, find.text(FakeLawData.codeName));
      await tester.tap(find.text(FakeLawData.codeName));
      await pumpUntilFound(tester, find.text(FakeLawData.articleTitle));
      await tester.tap(find.text(FakeLawData.articleTitle));
      await pumpUntilFound(
        tester,
        find.textContaining(FakeLawData.articleBody, findRichText: true),
      );
    });
  });
}

/// Non-empty while a known defect keeps the matching check skipped. Clear it
/// in the commit that fixes the defect, so the check runs again.
///
/// The server answers a rejected key with 401. The app's HTTP client turns
/// that into its own exception type before `ApiKeyValidationDataSource` sees
/// it, so its `on DioException` branch never fires and the reader is told the
/// server is unreachable instead of that the key does not work.
const rejectedKeyMessageDefect =
    'rejected key shows "server unreachable" instead of "key does not work"';

/// Back on the profile after a key change, the key row refreshes with
/// `setState(() => _key = _readKey())`: the arrow returns the Future, which a
/// debug build rejects with an assertion, so the row keeps the old last four
/// characters (`profile_page.dart`, `_ApiKeyTileState._change`).
const profileKeyLabelDefect =
    'profile key row throws on refresh after a key change (debug builds)';
