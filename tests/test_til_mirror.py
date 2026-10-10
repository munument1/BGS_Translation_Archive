"""Synthetic source extraction and ambiguity checks; no external requests."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('til_mirror', ROOT/'tools/import_til_mirror.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class MirrorTests(unittest.TestCase):
    def test_body_excludes_editorial_notes_preserves_unicode_and_paragraphs(self):
        body, notes = mod.extract('<div class="entry-content"><div class="librarian-comment">Editor note</div>'
                                  '<p>Wapna&#8217;s <em>book</em>.</p><p>Line 2<br>Line 3</p>'
                                  '<script>bad()</script></div>', True)
        self.assertEqual(body, 'Wapna’s book.\n\nLine 2\nLine 3')
        self.assertEqual(notes, 'Editor note')

    def test_ambiguous_title_not_guessed_and_translation_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mirror = root/'mirror'
            (mirror/'game-books').mkdir(parents=True)
            posts = mirror/'wp-json/wp/v2/posts'
            posts.mkdir(parents=True)
            for slug in ('two',):
                (posts/(slug+'.json')).write_text(json.dumps(dict(link=mod.SITE+'/content/'+slug,
                    content=dict(rendered='<p>Original text.</p>'))), encoding='utf-8')
            (mirror.parent/'hts-cache').mkdir()
            with ZipFile(mirror.parent/'hts-cache/new.zip', 'w') as cache:
                cache.writestr(mod.SITE+'/content/one', '<article><div class="entry-content"><p>Cached source.</p></div></article>')
            (mirror/'game-books/elder-scrolls-online-books.html').write_text(
                '<div class="entry-content"><a href="../content/one.html">Duplicate</a>'
                '<a href="../content/two.html">Duplicate</a></div>', encoding='utf-8')
            books = root/'docs/books'
            books.mkdir(parents=True)
            entries = [dict(uid='ambiguous',game='eso',title_en='Duplicate',source_url=mod.SITE+'/game-books/eso',direct_link=False),
                       dict(uid='exact',game='redguard',title_en='Exact',source_url=mod.SITE+'/content/one',direct_link=True)]
            (books/'imperial_game_books_catalog.json').write_text(json.dumps(dict(entries=entries)), encoding='utf-8')
            result = mod.run(mirror, root)
            self.assertEqual((result['imported'],result['ambiguous']), (1,1))
            target = root/'work/imperial_library_translation/redguard/exact.md'
            self.assertIn('Cached source.',target.read_text(encoding='utf-8'))
            target.write_text('Human translation', encoding='utf-8')
            mod.run(mirror, root)
            self.assertEqual(target.read_text(encoding='utf-8'), 'Human translation')


if __name__ == '__main__':
    unittest.main()
