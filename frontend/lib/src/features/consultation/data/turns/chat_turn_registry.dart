import 'dart:async';

/// One in-flight chat turn: the socket stream for a sent message, kept alive
/// independently of whichever screen started it.
///
/// A turn takes up to minutes. The screen that sent it can be popped, the
/// history sheet can swap the conversation out and back, the tab can change.
/// None of that should decide the turn's fate — the server finishes it either
/// way now — so the subscription lives here, in an app-level registry, and a
/// screen only ever *attaches* to it. Attaching replays what has happened so
/// far (stages, partial text, tool results) and then follows live.
class ChatTurn {
  ChatTurn({required this.conversationId, required this.streamingId});

  final String conversationId;

  /// The id of the assistant message this turn is filling in.
  final String streamingId;

  final List<Map<String, dynamic>> _events = [];
  final _live = StreamController<Map<String, dynamic>>.broadcast();
  bool _finished = false;

  bool get isFinished => _finished;

  void _add(Map<String, dynamic> event) {
    if (_finished) return;
    _events.add(event);
    _live.add(event);
    if (event['type'] == 'done' || event['type'] == 'error') _finish();
  }

  void _finish() {
    _finished = true;
    _live.close();
  }

  /// Every event so far, then the live ones. Built synchronously so no event
  /// can slip between the replay and the live subscription.
  Stream<Map<String, dynamic>> attach() {
    final out = StreamController<Map<String, dynamic>>();
    _events.forEach(out.add);
    if (_finished) {
      out.close();
    } else {
      final sub = _live.stream.listen(out.add, onDone: out.close);
      out.onCancel = sub.cancel;
    }
    return out.stream;
  }
}

class ChatTurnRegistry {
  final _turns = <String, ChatTurn>{};

  /// The turn still running for this conversation, if any.
  ChatTurn? active(String conversationId) {
    final turn = _turns[conversationId];
    return turn == null || turn.isFinished ? null : turn;
  }

  /// Start following [source] for [conversationId]. A stream that ends or
  /// fails without a terminal frame is turned into a connection error so no
  /// attached screen is left with the typing dots forever.
  ChatTurn start({
    required String conversationId,
    required Stream<Map<String, dynamic>> source,
  }) {
    final turn = ChatTurn(
      conversationId: conversationId,
      streamingId: 'stream_${DateTime.now().millisecondsSinceEpoch}',
    );
    _turns[conversationId] = turn;
    source.listen(
      turn._add,
      onError: (Object _) => turn._add(_connectionLost),
      onDone: () => turn._add(_connectionLost),
      cancelOnError: true,
    );
    return turn;
  }

  static const _connectionLost = <String, dynamic>{
    'type': 'error',
    'connection_lost': true,
  };
}
