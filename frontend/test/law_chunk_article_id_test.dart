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
      final ids = [
        'labour_code.chapter_I.article_1.chunk_0',
        'labour_code.chapter_I.article_1.chunk_1',
      ].map((id) => LawChunk.fromMap({'chunk_id': id}).articleId).toSet();

      expect(ids, {'labour_code.chapter_I.article_1'});
    });
  });

  group('LawChunk.bodyText', () {
    test('drops the embedding header, the source line and the disclaimer', () {
      final chunk = LawChunk.fromMap({
        'chunk_id': 'civil_code.article_532.chunk_0',
        'content':
            'საქართველოს სამოქალაქო კოდექსი | (#786) | თავი: თავი მესამე | მუხლი 532 | სათაური\n'
            'წყარო: https://matsne.gov.ge/ka/document/view/31702#article_532\n\n'
            'გამქირავებელი მოვალეა გადასცეს დამქირავებელს ნივთი.\n\n'
            'მეორე აბზაცი.\n\n'
            'ეს მასალა მხოლოდ საინფორმაციო მიზნებისთვისაა. ოფიციალური ტექსტისთვის იხილეთ matsne.gov.ge',
      });

      expect(
        chunk.bodyText,
        'გამქირავებელი მოვალეა გადასცეს დამქირავებელს ნივთი.\n\nმეორე აბზაცი.',
      );
    });

    test('leaves an unwrapped text alone', () {
      final chunk = LawChunk.fromMap({
        'chunk_id': 'x.article_1.chunk_0',
        'content': 'უბრალო ტექსტი',
      });
      expect(chunk.bodyText, 'უბრალო ტექსტი');
    });
  });
}
