"""Shared archive format must work for translations and untranslated sources."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('book_collection',ROOT/'tools/build_book_collection.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class FormatTests(unittest.TestCase):
    def test_existing_korean_markdown_unchanged(self):
        row=dict(title_ko='제목',book_id='ID1',author_ko='저자',ko='첫째\n둘째',source_ref='https://example.com')
        self.assertEqual(mod.render(row),'## 제목\n\nID: ID1 / 저자: 저자\n\n첫째  \n둘째\n\n[출처](https://example.com)\n\n---\n\n')

    def test_english_books_use_same_format_without_fake_korean(self):
        row=dict(title_en='A Book',title_ko='',book_id='ext-test',en='First\nSecond',source_ref='https://example.com')
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            result=mod.export(root,'battlespire',[row],language_label='원문·번역',game_label='Battlespire')
            self.assertEqual(result['books'],1)
            body=(root/'battlespire/books/A Book.md').read_text(encoding='utf-8')
            self.assertEqual(body,'# A Book\n\nID: ext-test\n\nFirst  \nSecond\n\n[출처](https://example.com)\n')
            self.assertNotIn('ko',row)
            self.assertTrue((root/'battlespire/complete.md').is_file())
            self.assertTrue((root/'battlespire/part-01.md').is_file())
            self.assertTrue((root/'battlespire/books.jsonl').is_file())
