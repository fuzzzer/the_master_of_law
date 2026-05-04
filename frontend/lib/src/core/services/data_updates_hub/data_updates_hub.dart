import 'dart:async';

final dataUpdatesHub = DataUpdatesHub();

class DataUpdatesHub {
  final StreamController<dynamic> _streamController;

  StreamController<dynamic> get streamController => _streamController;

  DataUpdatesHub({bool sync = false}) : _streamController = StreamController.broadcast(sync: sync);

  DataUpdatesHub.customController(StreamController<dynamic> controller) : _streamController = controller;

  Stream<T> on<T>() {
    if (T == dynamic) {
      return streamController.stream as Stream<T>;
    } else {
      return streamController.stream.where((event) => event is T).cast<T>();
    }
  }

  void sendNotification(dynamic notification) {
    _streamController.add(notification);
  }

  void destroy() {
    _streamController.close();
  }
}
