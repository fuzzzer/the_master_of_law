import 'package:flutter/material.dart';
import 'package:themasteroflaw/src/core/core.dart';

class NavigationLogger extends NavigatorObserver {
  @override
  void didPush(Route<dynamic> route, Route<dynamic>? previousRoute) {
    super.didPush(route, previousRoute);
    logger.i('Pushed: ${route.settings.name ?? "Unnamed Route"}');
  }

  @override
  void didPop(Route<dynamic> route, Route<dynamic>? previousRoute) {
    super.didPop(route, previousRoute);
    logger.i('Popped: ${route.settings.name ?? "Unnamed Route"}');
  }
}
