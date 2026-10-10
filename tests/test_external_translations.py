"""Imported text translations retain their scope, provenance and review state."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_external_book_collection import build


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / "docs/books"
        self.folder.mkdir(parents=True)
        self.sha = hashlib.sha256(b"Available excerpt.").hexdigest()
        self.source = dict(
            uid="new", game="redguard", title_en="An excerpt",
            body_en="Available excerpt.", source_url="https://example.com/excerpt",
            source_sha256=self.sha
        )
        legacy = dict(
            uid="legacy", game="shadowkey", title_en="Legacy",
            body_en="Original.", source_url="https://example.com/legacy",
            source_sha256=hashlib.sha256(b"Original.").hexdigest()
        )
        self.translation = dict(
            uid="new", game="redguard", title_ko="확보된 발췌문",
            coverage="available_source_text", body_ko="[발췌문]\n확보된 부분.",
            source_sha256=self.sha, needs_translation_review=True
        )
        self.write("external_english_texts.json", {"entries": [self.source, legacy]})
        self.write("external_korean_previews.json", {"entries": []})
        self.write("external_korean_texts.json", {"entries": [
            dict(uid="legacy", coverage="full", title_ko="기존 번역", body_ko="기존 본문."),
            dict(uid="new", coverage="fragment", title_ko="옛 발췌", body_ko="옛 참고문.")
        ]})
        self.write("external_korean_translations.json", {"entries": [self.translation]})
        (self.folder / "README.md").write_text("# Books\n", encoding="utf-8")

    def write(self, name, data):
        (self.folder / name).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def test_available_text_is_korean_without_claiming_book_completeness(self):
        legacy_bytes = (self.folder / "external_korean_texts.json").read_bytes()
        build(self.root)
        catalog = json.loads((self.folder / "additional_catalog.json").read_text(encoding="utf-8"))
        books = {b["uid"]: b for b in catalog["books"]}
        self.assertEqual(books["new"]["content_language"], "ko")
        self.assertEqual(books["new"]["translation_coverage"], "available_source_text")
        self.assertTrue(books["new"]["needs_translation_review"])
        self.assertNotIn("needs_translation_review", books["legacy"])
        self.assertEqual(
            (self.folder / books["new"]["path"]).read_text(encoding="utf-8"),
            "# 확보된 발췌문\n\nID: new\n\n[발췌문]  \n확보된 부분.\n\n[출처](https://example.com/excerpt)\n"
        )
        self.assertEqual((self.folder / "external_korean_texts.json").read_bytes(), legacy_bytes)
        exported = json.loads((self.folder / "redguard/books.jsonl").read_text(encoding="utf-8"))
        self.assertEqual(exported["en"], self.source["body_en"])
        self.assertEqual(exported["ko"], self.translation["body_ko"])
        self.assertTrue(exported["needs_translation_review"])
        self.assertIn("기존 본문.", (self.folder / books["legacy"]["path"]).read_text(encoding="utf-8"))

    def test_changed_source_blocks_stale_translation(self):
        self.translation["source_sha256"] = "wrong"
        self.write("external_korean_translations.json", {"entries": [self.translation]})
        with self.assertRaisesRegex(ValueError, "Translation source has changed"):
            build(self.root)

    def test_existing_full_translation_cannot_be_replaced(self):
        self.translation["uid"] = "legacy"
        self.write("external_korean_translations.json", {"entries": [self.translation]})
        with self.assertRaisesRegex(ValueError, "Existing full Korean translation must be preserved"):
            build(self.root)


class PublishedTranslationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = ROOT / "docs/books"
        cls.sources = {
            x["uid"]: x for x in json.loads(
                (cls.folder / "external_english_texts.json").read_text(encoding="utf-8")
            )["entries"]
        }
        cls.reference = json.loads(
            (cls.folder / "external_korean_texts.json").read_text(encoding="utf-8")
        )["entries"]
        cls.translations = json.loads(
            (cls.folder / "external_korean_translations.json").read_text(encoding="utf-8")
        )["entries"]

    def test_exact_requested_source_set_and_hashes(self):
        existing = {x["uid"] for x in self.reference if x.get("coverage") == "full"}
        expected = {
            uid for uid, row in self.sources.items()
            if row["game"] in {"battlespire", "redguard", "shadowkey"} and uid not in existing
        }
        self.assertEqual(len(expected), 67)
        self.assertEqual(len(self.translations), len(expected))
        self.assertEqual({x["uid"] for x in self.translations}, expected)
        for row in self.translations:
            with self.subTest(uid=row["uid"]):
                source = self.sources[row["uid"]]
                for key in ("game", "title_en", "source_url", "source_sha256"):
                    self.assertEqual(row[key], source[key])
                self.assertEqual(row["coverage"], "available_source_text")
                self.assertTrue(row["needs_translation_review"])
                self.assertTrue(row["body_ko"].strip())

    def test_catalog_and_common_outputs_include_the_translation(self):
        catalog = json.loads(
            (self.folder / "additional_catalog.json").read_text(encoding="utf-8")
        )["books"]
        books = {x["uid"]: x for x in catalog}
        for row in self.translations:
            with self.subTest(uid=row["uid"]):
                book = books[row["uid"]]
                self.assertEqual(book["content_language"], "ko")
                self.assertTrue(book["needs_translation_review"])
                self.assertEqual(book["translation_coverage"], "available_source_text")
                markdown = (self.folder / book["path"]).read_text(encoding="utf-8")
                self.assertIn(row["body_ko"].replace("\n", "  \n"), markdown)
        for row in self.reference:
            if row.get("coverage") == "full":
                markdown = (self.folder / books[row["uid"]]["path"]).read_text(encoding="utf-8")
                self.assertIn(row["body_ko"].replace("\n", "  \n"), markdown)

    def test_codex_preserves_all_nine_volumes_and_named_entries(self):
        import re
        source = self.sources["ext-69c8a880f83f8e170930"]["body_en"]
        translated = next(
            x["body_ko"] for x in self.translations if x["uid"] == "ext-69c8a880f83f8e170930"
        )
        volumes = re.findall(r"^Codex Arcana, Volume ([IVX]+)$", source, re.MULTILINE)
        self.assertEqual(len(volumes), 9)
        for number in range(1, len(volumes) + 1):
            self.assertEqual(translated.count(f"비전 대전, 제{number}권"), 1)
        names = re.findall(r"^“([^”]+)”$", source, re.MULTILINE)
        names += [
            p.split(":", 1)[0] for p in source.split("\n\n")
            if "\n" not in p and ":" in p
        ]
        for name in names:
            with self.subTest(name=name):
                self.assertEqual(translated.count("(" + name + ")"), 1)
