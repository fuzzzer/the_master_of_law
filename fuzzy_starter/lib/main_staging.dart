import 'package:flutter/material.dart';
import 'src/src.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  appEnvironment = Environment.development;
  await Environment.initialize();

  FuzzystarterApp.run();
}
