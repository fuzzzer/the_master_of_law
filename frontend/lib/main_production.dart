import 'package:flutter/material.dart';
import 'src/src.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  appEnvironment = Environment.production;
  await Environment.initialize();

  FuzzzyLawApp.run();
}
