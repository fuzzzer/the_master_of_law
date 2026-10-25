import 'package:integration_test/integration_test.dart';

import '../test/app_flows/app_flows.dart';

/// The same app flows on a real device, emulator or browser:
/// `scripts/run_app_flows.sh -d <device>`.
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  defineAppFlows();
}
