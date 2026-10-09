"""Synthetic regression tests. No Bethesda game files are used."""
import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("skyrim_book_extractor", ROOT / "tools" / "extract_skyrim_books.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def record(tag, raw=b"", flags=0, form_id=0):
    return struct.pack("<4sIIIII", tag, len(raw), flags, form_id, 0, 0) + raw


def subrecord(tag, raw):
    return tag + struct.pack("<H", len(raw)) + raw


def string_table(sid, text, with_length=False):
    raw = text.encode("utf-8") + b"\0"
    if with_length:
        raw = struct.pack("<I", len(raw)) + raw
    return struct.pack("<IIII", 1, len(raw), sid, 0) + raw


class SkyrimBookTests(unittest.TestCase):
    def test_localized_book_only(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / "strings").mkdir()
            body = (subrecord(b"EDID", b"BookSample\0")
                    + subrecord(b"FULL", struct.pack("<I", 0x10))
                    + subrecord(b"DESC", struct.pack("<I", 0x20)))
            sample = record(b"BOOK", body, form_id=0x000AB123)
            other = record(b"INFO", subrecord(b"NAM1",struct.pack("<I",0x20)))
            grp = b"GRUP" + struct.pack("<I", 24 + len(sample) + len(other)) + b"\0" * 16
            plugin = record(b"TES4", flags=0x80) + grp + sample + other
            (home / "Skyrim.esm").write_bytes(plugin)
            (home / "strings" / "Skyrim_english.STRINGS").write_bytes(string_table(0x10, "붉은 책"))
            (home / "strings" / "Skyrim_english.DLSTRINGS").write_bytes(
                string_table(0x20, "책의 본문\n둘째 줄", with_length=True))
            output = home / "skyrim_book_records.jsonl"
            mod.run(home, output)
            result = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["form_id"], "000AB123")
            self.assertEqual(result[0]["title_ko"], "붉은 책")
            self.assertEqual(result[0]["ko"], "책의 본문\n둘째 줄")
            self.assertEqual(result[0]["record"], "BOOK")
            self.assertEqual(result[0]["text_string_id"], 0x20)

    def test_strings_alone_fail_clearly(self):
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            (home / "strings").mkdir()
            with self.assertRaisesRegex(ValueError, "No Skyrim"):
                mod.run(home, home / "out.jsonl")


if __name__ == "__main__":
    unittest.main()
