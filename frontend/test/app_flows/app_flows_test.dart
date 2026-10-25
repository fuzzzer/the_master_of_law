import 'package:flutter_test/flutter_test.dart';

import 'app_flows.dart';

/// The app flows without a device: `fvm flutter test test/app_flows`.
void main() {
  TestWidgetsFlutterBinding.ensureInitialized();
  defineAppFlows();
}
