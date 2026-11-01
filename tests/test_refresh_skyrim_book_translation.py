import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from refresh_skyrim_book_translation import (
    read_dictionary, prepare, load_archive, write_shards, old_key, unique_field,
)

SHA = "dc1796e26f5b3d1db0e1116c5a0b04a13759dba9"


def row(fid="0001ACB9", text="기존 글", plugin="Skyrim.esm"):
    return {"plugin": plugin, "form_id": fid, "book_id": fid,
            "editor_id": "MyBook", "title_ko": "기존 제목", "ko": text,
            "record": "BOOK", "field": "DESC"}


class RefreshDictionaryTests(unittest.TestCase):
    def make_dictionary(self, file):
        data = "\n".join([
            "XTranslatorAi-GameStrings-v2",
            "F\tBOOK/skyrim.esm:01ACB9/0/DESC/0\t" + "a"*32 +
            "\t갱신된\\n본문\tSkyrim.esm",
            "F\tBOOK/skyrim.esm:01ACB9/0/FULL/0\t" + "b"*32 +
            "\t새 제목\tSkyrim.esm",
            "F\tBOOK/skyrim.esm:020000/0/DESC/0\t" + "c"*32 +
            "\t새 책\tUpdate.esm",
            "T\ttesthash\t안쓰는 번역",
            ""
        ])
        with gzip.open(file, "wt", encoding="utf-8") as stream:
            stream.write(data)

    def test_read_real_format_and_decode(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "game-strings.gz"
            self.make_dictionary(file)
            groups, counts = read_dictionary(file)
            self.assertEqual(counts["DESC"], 2)
            self.assertEqual(groups[("skyrim.esm", "01ACB9")]["DESC"][0][0], "갱신된\n본문")
            self.assertEqual(groups[("skyrim.esm", "01ACB9")]["FULL"][0][0], "새 제목")

    def test_existing_books_and_new_holds(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "dictionary.gz"
            self.make_dictionary(file)
            dictionary, _ = read_dictionary(file)
            original = row()
            old = {old_key(original): original}
            rows, report = prepare(old, dictionary, SHA)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["ko"], "갱신된\n본문")
            self.assertEqual(rows[0]["title_ko"], "새 제목")
            self.assertEqual(report["counts"]["changed"], 1)
            self.assertEqual(report["counts"]["new_identity_candidates"], 1)
            self.assertEqual(len([r for r in report["review"] if r["reason"].startswith("new_identity")]), 1)

    def test_ambiguous_and_tag_mismatch_preserved(self):
        original = row(text="<Alias=Jarl>에게")
        k = old_key(original)
        dict_ = {k: {"DESC": [("딴 글", "a"*32, "Skyrim.esm"),
                              ("또 다른 글", "b"*32, "Update.esm")]}}
        updated, report = prepare({k: original}, dict_, SHA)
        self.assertEqual(updated[0]["ko"], original["ko"])
        self.assertEqual(report["counts"]["ambiguous_held"], 1)
        dict_ = {k: {"DESC": [("<Alias=Different>에게", "a"*32, "Skyrim.esm")]}}
        updated, report = prepare({k: original}, dict_, SHA)
        self.assertEqual(updated[0]["ko"], original["ko"])
        self.assertEqual(report["counts"]["tag_mismatch_held"], 1)

    def test_identity_collision_and_shards(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            write_shards([row(), row("0001ACBA", "다른 글")], folder)
            self.assertEqual(len(load_archive(folder)), 2)
            with (folder/"skyrim_books_999.jsonl").open("w", encoding="utf-8") as f:
                f.write(json.dumps(row(), ensure_ascii=False) + "\n")
            with self.assertRaisesRegex(ValueError, "Duplicate archive key"):
                load_archive(folder)

    def test_bad_revision_and_bad_gzip(self):
        with self.assertRaisesRegex(ValueError, "full lowercase SHA"):
            prepare({}, {}, "main")
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.gz"
            with gzip.open(bad, "wt", encoding="utf-8") as f:
                f.write("wrong-header\n")
            with self.assertRaisesRegex(ValueError, "Unrecognized"):
                read_dictionary(bad)


if __name__ == "__main__":
    unittest.main()
