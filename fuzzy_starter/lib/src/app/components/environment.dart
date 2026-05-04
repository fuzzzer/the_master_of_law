import 'package:flutter_dotenv/flutter_dotenv.dart';

late final Environment appEnvironment;

enum Environment {
  production,
  staging,
  development;

  bool get isProduction => this == Environment.production;

  bool get isStaging => this == Environment.staging;

  bool get isDevelopment => this == Environment.development;

  static Future<void> initialize() async {
    await dotenv.load(fileName: getEnvFileName());
  }

  static String getEnvFileName() {
    return switch (appEnvironment) {
      production => 'env/env.production',
      staging => 'env/env.staging',
      development => 'env/env.development',
    };
  }
}
