import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:marionette_flutter/marionette_flutter.dart';
import 'src/src.dart';

Future<void> main() async {
  if (kDebugMode) {
    MarionetteBinding.ensureInitialized();
  } else {
    WidgetsFlutterBinding.ensureInitialized();
  }
  appEnvironment = Environment.development;
  await Environment.initialize();

  ThemasteroflawApp.run();
}
