import 'dart:async';
import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_law/src/features/consultation/data/data.dart';

void main() {
  test(
    'heartbeats keep a slow turn alive past the silence window, and the '
    'answer still arrives',
    () async {
      final socket = StreamController<dynamic>();
      final frames = <Map<String, dynamic>>[];
      final done = turnFrames(
        socket.stream,
        silence: const Duration(milliseconds: 60),
      ).forEach(frames.add);

      // 300 ms of model work — five silence windows — with a beat every 20 ms.
      for (var i = 0; i < 15; i++) {
        await Future<void>.delayed(const Duration(milliseconds: 20));
        socket.add(jsonEncode({'type': 'heartbeat'}));
      }
      socket.add(jsonEncode({'type': 'done', 'full_response': 'პასუხი'}));
      await done;

      expect(frames.last['type'], 'done');
      expect(frames.any((f) => f['type'] == 'error'), isFalse);
    },
  );

  test(
    'a server that really goes silent ends the stream without inventing an '
    'error, so the turn is looked up on the server instead',
    () async {
      final socket = StreamController<dynamic>();
      final frames = <Map<String, dynamic>>[];
      await turnFrames(
        socket.stream,
        silence: const Duration(milliseconds: 30),
      ).forEach(frames.add);

      expect(frames, isEmpty, reason: 'no English "timeout" bubble');
    },
  );
}
