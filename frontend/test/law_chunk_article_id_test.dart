import 'package:flutter_test/flutter_test.dart';
import 'package:fuzzzy_law/src/src.dart';

void main() {
  group('LawChunk.articleId', () {
    test('is the chunk id without its chunk suffix, never the label', () {
      final chunk = LawChunk.fromMap({
        'chunk_id': 'admin_offences_code.article_1.chunk_0',
        'content': '…',
        'metadata': {'article_number': 'მუხლი 1'},
      });

      expect(chunk.articleId, 'admin_offences_code.article_1');
      expect(chunk.articleNumber, 'მუხლი 1');
    });

    test('survives chapter segments in the chunk id', () {
      final chunk = LawChunk.fromMap({
        'chunk_id': 'constitution.chapter_თავი პირველი.article_1.chunk_2',
      });

      expect(chunk.articleId, 'constitution.chapter_თავი პირველი.article_1');
    });

    test('groups every chunk of one article under the same id', () {
      final ids = ['labour_code.chapter_I.article_1.chunk_0', 'labour_code.chapter_I.article_1.chunk_1']
          .map((id) => LawChunk.fromMap({'chunk_id': id}).articleId)
          .toSet();

      expect(ids, {'labour_code.chapter_I.article_1'});
    });
  });
}
