import 'package:hive_flutter/adapters.dart';
import 'package:hive_flutter/hive_flutter.dart';

export 'constants/constants.dart';

class ApiCacheService {
  static final ApiCacheService _instance = ApiCacheService._internal();
  late final Box<dynamic> box;

  factory ApiCacheService() {
    return _instance;
  }

  ApiCacheService._internal();

  Future<void> init() async {
    await Hive.initFlutter();
    // Register adapters when needed
    // Hive.registerAdapter(CustomLocalStorageClass());
  }
}
