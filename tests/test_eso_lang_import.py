"""ESO import bounds, conservative matching, formatting and published links."""
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from import_eso_korean_lang import read_books,plain_text,title_key

class LangTests(unittest.TestCase):
    def test_keyed_utf8_and_bounds(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'kr.lang';text='책 제목\0책 본문\0'.encode()
            offset=len('책 제목\0'.encode())
            p.write_bytes(struct.pack('>II',2,2)+struct.pack('>4I',51188213,0,7,0)+struct.pack('>4I',21337012,0,7,offset)+text)
            rows,source=read_books(p)
            self.assertEqual(rows[(21337012,7)],'책 본문')
            self.assertEqual(source['file_sha256'],hashlib.sha256(p.read_bytes()).hexdigest())
            p.write_bytes(struct.pack('>II',2,8))
            with self.assertRaises(ValueError):read_books(p)
    def test_alignment_does_not_eat_paragraphs(self):
        raw='|ac첫 문단\n\n|ac둘째 문단|r\n|cffffff본문|r\n<<1>>\n|t10:20:map.dds|t'
        self.assertEqual(plain_text(raw),'첫 문단\n\n둘째 문단\n본문\n<<1>>\n[게임 내 삽화]')
    def test_title_matching_preserves_volume_numbers(self):
        self.assertEqual(title_key('A Cat’s Tale [ESO]'),title_key("A Cat's Tale"))
        self.assertNotEqual(title_key('Book II'),title_key('Book III'))
    def test_published_imports_keep_identifiers_and_outputs(self):
        folder=ROOT/'docs/books'
        data=json.loads((folder/'eso_korean_imports.json').read_text(encoding='utf-8'))
        catalog={r['uid']:r for r in json.loads((folder/'additional_catalog.json').read_text(encoding='utf-8'))['books']}
        sources={r['uid']:r for r in json.loads((folder/'external_english_texts.json').read_text(encoding='utf-8'))['entries']}
        fulltext={r['uid']:r['text'] for r in json.loads((folder/'additional_fulltext-index.json').read_text(encoding='utf-8'))}
        self.assertEqual(len(data['entries']),3847)
        for row in data['entries']:
            with self.subTest(uid=row['uid']):
                book=catalog[row['uid']]
                self.assertEqual(book['eso_book_id'],row['eso_book_id'])
                self.assertEqual(book['content_language'],'ko')
                self.assertEqual(book['translation_coverage'],'existing_game_record')
                self.assertEqual(row['source_sha256'],sources.get(row['uid'],{}).get('source_sha256'))
                self.assertEqual(fulltext[row['uid']],row['body_ko'])
                self.assertIn(row['body_ko'].replace('\n','  \n'),(folder/book['path']).read_text(encoding='utf-8'))
                self.assertNotIn('\ufffd',row['body_ko'])
                self.assertTrue(row['body_ko'].strip())
        report=json.loads((folder/'eso_korean_import_report.json').read_text(encoding='utf-8'))
        self.assertEqual(report['imported'],len(data['entries']))
        self.assertEqual(sum(report['deferred_counts'].values())+report['imported'],4766)
        excluded={r['uid'] for r in report['deferred']}
        self.assertFalse(excluded & {r['uid'] for r in data['entries']})

if __name__=='__main__':unittest.main()
