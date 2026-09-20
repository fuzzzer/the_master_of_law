import 'dart:async';

import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_law/src/core/core.dart';
import 'package:fuzzzy_law/src/features/consultation/bloc/bloc.dart';
import 'package:fuzzzy_law/src/features/consultation/data/data.dart';

class _FakeSource implements ConsultationRemoteDataSource {
  final socket = StreamController<Map<String, dynamic>>();
  final List<Map<String, dynamic>> stored = [];
  int conversationReads = 0;
  bool turnInProgress = false;

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
  Future<Map<String, dynamic>> getConversation(String conversationId) async {
    conversationReads++;
    return {
      'id': conversationId,
      'messages': stored,
      'case_ready': false,
      'turn_in_progress': turnInProgress,
    };
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

ConsultationCubit _cubitFor(_FakeSource source) =>
    ConsultationCubit(
      repository: ConsultationRepository(remoteDataSource: source),
      turns: ChatTurnRegistry(),
      recoveryPollInterval: Duration.zero,
    )..emit(
      const ConsultationState(
        status: StateStatus.success,
        conversationId: 'c1',
      ),
    );

void main() {
  test(
    "a server-reported error keeps the server's sentence and carries no "
    'failureType, so the bubble shows why instead of "unknown error"',
    () async {
      final source = _FakeSource();
      final cubit =
          ConsultationCubit(
            repository: ConsultationRepository(remoteDataSource: source),
            turns: ChatTurnRegistry(),
          )..emit(
            const ConsultationState(
              status: StateStatus.success,
              conversationId: 'c1',
            ),
          );
      unawaited(cubit.sendMessage('რაა?'));
      await Future<void>.delayed(Duration.zero);

      const quota =
          'AI სერვისის დღიური ლიმიტი ამოიწურა. გთხოვთ, სცადოთ მოგვიანებით.';
      source.socket.add({
        'type': 'error',
        'code': 'ai_quota_exhausted',
        'message': quota,
        'retry_after_s': 57,
      });
      await Future<void>.delayed(Duration.zero);

      final bubble = cubit.state.messages.last;
      expect(bubble.isError, isTrue);
      expect(bubble.text, quota);
      expect(bubble.failureType, isNull);
      expect(cubit.state.isSending, isFalse);
      await cubit.close();
    },
  );

  test(
    'a socket that drops mid-turn is not an error: the answer that the '
    'server finished without us is fetched and shown',
    () async {
      final source = _FakeSource();
      final cubit = _cubitFor(source);
      unawaited(cubit.sendMessage('რაა?'));
      await Future<void>.delayed(Duration.zero);

      // The user's message is on the server; the answer is not yet.
      source
        ..turnInProgress = true
        ..stored.add({'id': 'u1', 'role': 'user', 'content': 'რაა?'});
      await source.socket.close();
      await Future<void>.delayed(Duration.zero);
      expect(cubit.state.isSending, isTrue, reason: 'still waiting');
      expect(cubit.state.messages.any((m) => m.isError), isFalse);

      // Two polls later the server has it.
      await Future<void>.delayed(Duration.zero);
      source
        ..stored.add({'id': 'a1', 'role': 'assistant', 'content': 'პასუხი'})
        ..turnInProgress = false;
      await Future<void>.delayed(const Duration(milliseconds: 10));

      expect(cubit.state.isSending, isFalse);
      expect(cubit.state.messages.last.text, 'პასუხი');
      expect(cubit.state.messages.any((m) => m.isError), isFalse);
      expect(source.conversationReads, greaterThanOrEqualTo(2));
      await cubit.close();
    },
  );

  test('closing the screen stops the polling', () async {
    final source = _FakeSource()..turnInProgress = true;
    final cubit = _cubitFor(source);
    unawaited(cubit.sendMessage('რაა?'));
    await Future<void>.delayed(Duration.zero);
    await source.socket.close();
    await Future<void>.delayed(const Duration(milliseconds: 5));
    await cubit.close();
    final readsAtClose = source.conversationReads;
    await Future<void>.delayed(const Duration(milliseconds: 20));

    expect(source.conversationReads, lessThanOrEqualTo(readsAtClose + 1));
  });

  test(
    'a page opened while the server is still writing the answer waits for '
    'it instead of showing question-and-silence',
    () async {
      final source = _FakeSource()
        ..turnInProgress = true
        ..stored.add({'id': 'u1', 'role': 'user', 'content': 'კითხვა'});
      final cubit = ConsultationCubit(
        repository: ConsultationRepository(remoteDataSource: source),
        turns: ChatTurnRegistry(),
        recoveryPollInterval: Duration.zero,
      );
      await cubit.loadConversation('c1');
      expect(cubit.state.isSending, isTrue, reason: 'told to wait');

      await Future<void>.delayed(Duration.zero);
      source
        ..stored.add({'id': 'a1', 'role': 'assistant', 'content': 'პასუხი'})
        ..turnInProgress = false;
      await Future<void>.delayed(const Duration(milliseconds: 10));

      expect(cubit.state.isSending, isFalse);
      expect(cubit.state.messages.map((m) => m.text), ['კითხვა', 'პასუხი']);
      await cubit.close();
    },
  );

  test(
    'a turn that failed while we were away shows the stored failure as an '
    'error bubble with its own sentence',
    () async {
      final source = _FakeSource();
      final cubit = _cubitFor(source);
      unawaited(cubit.sendMessage('რაა?'));
      await Future<void>.delayed(Duration.zero);
      source
        ..turnInProgress = true
        ..stored.add({'id': 'u1', 'role': 'user', 'content': 'რაა?'});
      await source.socket.close();
      await Future<void>.delayed(Duration.zero);

      const quota =
          'AI სერვისის დღიური ლიმიტი ამოიწურა. სცადეთ მოგვიანებით ან სხვა მოდელით.';
      source
        ..stored.add({'id': 'e1', 'role': 'error', 'content': quota})
        ..turnInProgress = false;
      await Future<void>.delayed(const Duration(milliseconds: 10));

      final last = cubit.state.messages.last;
      expect(cubit.state.isSending, isFalse);
      expect(last.isError, isTrue);
      expect(last.isUser, isFalse);
      expect(last.text, quota);
      expect(last.failureType, isNull, reason: 'the sentence is the message');
      await cubit.close();
    },
  );
}
