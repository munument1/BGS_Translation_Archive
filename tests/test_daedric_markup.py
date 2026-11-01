import unittest
from tools.build_book_collection import norm, mark_daedric_faces


class DaedricMarkupTests(unittest.TestCase):
    def test_daedric_font_preserves_original_glyph_text(self):
        self.assertEqual(
            norm('<font face="Daedric">ABCD</font> 한국어', preserve_daedric=True),
            '[daedric]ABCD[/daedric] 한국어',
        )

    def test_nested_size_tags_do_not_end_daedric_span(self):
        original = '<font face="DemonicLetters">AY<font size="20">EM</font>BD</font>다음'
        self.assertEqual(
            norm(original, preserve_daedric=True),
            '[daedric]AYEMBD[/daedric]다음',
        )

    def test_other_font_names_remain_plain(self):
        text = '<font face="$HandwrittenFont">안녕하세요</font>'
        self.assertEqual(norm(text, preserve_daedric=True), '안녕하세요')

    def test_font_switches_only_wrap_daedric_part(self):
        text = "<font face='Daedric'>AB<font face='Normal'>한글</font>CD</font>"
        self.assertEqual(
            norm(text, preserve_daedric=True),
            '[daedric]AB[/daedric]한글[daedric]CD[/daedric]',
        )

    def test_unclosed_font_has_explicit_marker_end(self):
        self.assertEqual(mark_daedric_faces('<font face="Ayembedt">ABC'), '[daedric]ABC[/daedric]')

    def test_default_existing_formatting_unchanged(self):
        self.assertEqual(norm('<font face="Daedric">ABC</font>'), 'ABC')

    def test_non_font_tags_are_not_activated(self):
        self.assertEqual(norm('<p>Daedric alphabet, ABC</p>', preserve_daedric=True),
                         'Daedric alphabet, ABC')


if __name__=="__main__":
    unittest.main()
