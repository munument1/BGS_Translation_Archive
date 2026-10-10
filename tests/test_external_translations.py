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

    def test_review_distinguishes_source_comparison_from_unresolved_text(self):
        self.write("external_korean_translations.json", {
            "review": {"method": "ai_source_comparison", "reviewed_uids": ["new"],
                       "unresolved": {"new": "원본 이미지 확인 필요"}},
            "entries": [self.translation]
        })
        build(self.root)
        books = json.loads((self.folder / "additional_catalog.json").read_text(encoding="utf-8"))["books"]
        book = next(b for b in books if b["uid"] == "new")
        self.assertEqual(book["translation_review"], "needs_source_check")
        self.assertEqual(book["review_method"], "ai_source_comparison")
        self.assertEqual(book["review_notes"], "원본 이미지 확인 필요")
        self.assertTrue(book["needs_translation_review"])
        self.write("external_korean_translations.json", {
            "review": {"method": "ai_source_comparison", "reviewed_uids": ["new"], "unresolved": {}},
            "entries": [self.translation]
        })
        build(self.root)
        books = json.loads((self.folder / "additional_catalog.json").read_text(encoding="utf-8"))["books"]
        book = next(b for b in books if b["uid"] == "new")
        self.assertEqual(book["translation_review"], "source_compared")
        self.assertEqual(book["review_notes"], "")
        self.assertTrue(book["needs_translation_review"], "AI comparison does not claim human review")

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

    def test_review_covers_exactly_the_available_translations(self):
        data = json.loads((self.folder / "external_korean_translations.json").read_text(encoding="utf-8"))
        review = data["review"]
        ids = {row["uid"] for row in self.translations}
        self.assertEqual(set(review["reviewed_uids"]), ids)
        self.assertEqual(len(review["reviewed_uids"]), len(ids))
        self.assertTrue(set(review["unresolved"]) <= ids)
        self.assertEqual(review["method"], "ai_source_comparison")
        books = {
            x["uid"]: x for x in json.loads(
                (self.folder / "additional_catalog.json").read_text(encoding="utf-8")
            )["books"]
        }
        for row in self.translations:
            with self.subTest(uid=row["uid"]):
                self.assertNotIn("\ufffd", row["body_ko"])
                self.assertNotIn("\ufffd", row["title_ko"])
                expected = "needs_source_check" if row["uid"] in review["unresolved"] else "source_compared"
                self.assertEqual(books[row["uid"]]["translation_review"], expected)
                self.assertTrue(books[row["uid"]]["needs_translation_review"])
                self.assertEqual(books[row["uid"]]["review_notes"], review["unresolved"].get(row["uid"], ""))

    def test_cipher_and_numeric_clues_are_preserved_from_the_source(self):
        import re
        translations = {x["uid"]: x["body_ko"] for x in self.translations}
        for uid in (
            "ext-624381df414cf9d33dcf", "ext-9cb02ea71d6096f40a0b",
            "ext-1c57abb1320abd00eff4", "ext-6da2228c392847c44ec1"
        ):
            source = self.sources[uid]["body_en"]
            quoted = re.findall(r"\b[A-Z]{2,}(?:-[A-Z]+)*\b|\b\d+(?:-\d+)+\b", source)
            for literal in quoted:
                with self.subTest(uid=uid, literal=literal):
                    self.assertIn(literal, translations[uid])
        for uid in ("ext-f8fc052fab5bdd6b3dd4", "ext-fded7edea602adab5128"):
            for literal in re.findall(r"\d+(?:\.\d+)?", self.sources[uid]["body_en"]):
                with self.subTest(uid=uid, literal=literal):
                    self.assertIn(literal, translations[uid])
