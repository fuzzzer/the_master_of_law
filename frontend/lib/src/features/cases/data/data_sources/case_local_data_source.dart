import 'package:hive/hive.dart';
import 'package:themasteroflaw/src/src.dart';

/// Local Hive data source for case CRUD operations.
class CaseLocalDataSource {
  static const _boxName = 'cases';

  Future<Box<CaseData>> _openBox() async {
    if (Hive.isBoxOpen(_boxName)) {
      return Hive.box<CaseData>(_boxName);
    }
    return Hive.openBox<CaseData>(_boxName);
  }

  Future<List<CaseData>> getAllCases() async {
    final box = await _openBox();
    return box.values.toList()
      ..sort((a, b) => b.updatedAt.compareTo(a.updatedAt));
  }

  Future<CaseData?> getCaseById(String id) async {
    final box = await _openBox();
    return box.get(id);
  }

  Future<void> saveCase(CaseData caseData) async {
    final box = await _openBox();
    await box.put(caseData.id, caseData);
  }

  Future<void> deleteCase(String id) async {
    final box = await _openBox();
    await box.delete(id);
  }
}
