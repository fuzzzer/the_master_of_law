import 'dart:async';

import 'package:flutter/foundation.dart';

/// Emitted on the global `dataUpdatesHub` when the server rejects the stored
/// API key (HTTP 401). The app shell reacts by routing back to the key prompt.
class UnauthorizedEvent {
  const UnauthorizedEvent();
}

/// Adapts a [Stream] into a [Listenable] so GoRouter can use it as a
/// `refreshListenable` and re-run its redirect when the stream emits.
class GoRouterRefreshStream extends ChangeNotifier {
  GoRouterRefreshStream(Stream<dynamic> stream) {
    notifyListeners();
    _subscription = stream.asBroadcastStream().listen((_) => notifyListeners());
  }

  late final StreamSubscription<dynamic> _subscription;

  @override
  void dispose() {
    _subscription.cancel();
    super.dispose();
  }
}
