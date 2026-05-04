import 'package:flutter_secure_storage/flutter_secure_storage.dart';

export 'secure_storage_service_keys.dart';

class SecureStorageService {
  SecureStorageService(this._flutterSecureStorage);

  final FlutterSecureStorage _flutterSecureStorage;

  Future<String?> getData(String key) async =>
      _secureStorageHelper(() async => await _flutterSecureStorage.read(key: key));

  Future<void> saveData(String key, String value) async {
    await _secureStorageHelper(() => _flutterSecureStorage.write(key: key, value: value));
  }

  Future<void> deleteData(String key) async {
    await _secureStorageHelper(() => _flutterSecureStorage.delete(key: key));
  }

  Future<void> clearAllSecureData() async {
    await _secureStorageHelper(_flutterSecureStorage.deleteAll);
  }

  Future<T> _secureStorageHelper<T>(Future<T> Function() operation) async {
    try {
      return await operation();
    } catch (e) {
      throw Exception('Failed to perform secure storage operation: $e');
    }
  }
}
