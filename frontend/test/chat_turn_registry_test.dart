import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_law/src/core/core.dart';
import 'package:fuzzzy_law/src/features/consultation/bloc/bloc.dart';
import 'package:fuzzzy_law/src/features/consultation/data/data.dart';

/// Stands in for the socket. Only the two calls the scenario needs exist;
/// anything else is a programming error the test should surface.
class _FakeSource implements ConsultationRemoteDataSource {
  final socket = StreamController<Map<String, dynamic>>();
  final List<Map<String, dynamic>> stored = [];

  @override
  Stream<Map<String, dynamic>> streamMessage({
    required String conversationId,
    required String message,
    Map<String, dynamic>? ragConfig,
    String mode = 'chat',
    String? caseContext,
    String? caseFileId,
  }) => socket.stream;

  @override
  Future<Map<String, dynamic>> getConversation(String conversationId) async => {
    'id': conversationId,
    'messages': stored,
    'case_ready': false,
  };

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  group('ChatTurnRegistry', () {
    test(
      'attaching late replays every frame so far, then follows live',
      () async {
        final registry = ChatTurnRegistry();
        final source = StreamController<Map<String, dynamic>>();
        final turn = registry.start(
          conversationId: 'c1',
          source: source.stream,
        );

        source.add({'type': 'stage', 'index': 1});
        source.add({'type': 'chunk', 'content': 'ნახე'});
        await Future<void>.delayed(Duration.zero);

        final seen = <String>[];
        final sub = turn.attach().listen((e) => seen.add(e['type'] as String));
        source.add({'type': 'done', 'full_response': 'ნახევარი'});
        await Future<void>.delayed(Duration.zero);

        expect(seen, ['stage', 'chunk', 'done']);
        expect(registry.active('c1'), isNull, reason: 'a done turn is over');
        await sub.cancel();
      },
    );

    test(
      'a socket that closes without a terminal frame becomes an error',
      () async {
        final registry = ChatTurnRegistry();
        final source = StreamController<Map<String, dynamic>>();
        final turn = registry.start(
          conversationId: 'c1',
          source: source.stream,
        );
        await source.close();
        await Future<void>.delayed(Duration.zero);

        final last = await turn.attach().last;
        expect(last['type'], 'error');
        expect(last['connection_lost'], isTrue);
      },
    );
  });

  group('ConsultationCubit with a turn that outlives it', () {
    test(
      'the screen that sent the message is disposed; the next one that '
      'opens the conversation shows the progress and receives the answer',
      () async {
        final registry = ChatTurnRegistry();
        final source = _FakeSource();
        final repository = ConsultationRepository(remoteDataSource: source);

        final first = ConsultationCubit(repository: repository, turns: registry)
          ..emit(
            const ConsultationState(
              status: StateStatus.success,
              conversationId: 'c1',
            ),
          );
        unawaited(first.sendMessage('კითხვა'));
        await Future<void>.delayed(Duration.zero);
        source.socket.add({
          'type': 'stage',
          'key': 'retrieve',
          'label': 'ძიება',
          'index': 2,
          'total': 10,
        });
        await Future<void>.delayed(Duration.zero);
        expect(first.state.stage?.index, 2);

        // Back button, tab change, whatever: the screen and its cubit go away.
        await first.close();

        // The server has the user's message by now; the answer is still coming.
        source.stored.add({
          'id': 'm1',
          'role': 'user',
          'content': 'კითხვა',
          'created_at': '2026-09-20T00:00:00Z',
        });
        final second = ConsultationCubit(
          repository: repository,
          turns: registry,
        );
        await second.loadConversation('c1');
      await Future<void>.delayed(Duration.zero);

        expect(
          second.state.isSending,
          isTrue,
          reason: 'the turn is still running',
        );
        expect(second.state.stage?.index, 2, reason: 'progress replayed');
        expect(second.state.messages.map((m) => m.text), ['კითხვა']);

        source.socket.add({'type': 'chunk', 'content': 'პასუხი'});
        source.socket.add({
          'type': 'done',
          'full_response': 'პასუხი',
          'citations': <dynamic>[],
        });
        await Future<void>.delayed(Duration.zero);

        expect(second.state.isSending, isFalse);
        expect(second.state.messages.map((m) => m.text), ['კითხვა', 'პასუხი']);
        await second.close();
      },
    );
  });
}
