"""Boundary tests: never confuse English hashes or merge distinct table IDs.

Run from repo root: python -m unittest discover -s tools -p test_translation_memory.py
"""
import hashlib
import unittest

from translation_memory import normalized, stable_identity


class TestTranslationMemoryBoundaries(unittest.TestCase):
    def test_actual_sst_english_hash_is_kept(self):
        english="Slaughterfish"
        expected=hashlib.sha256(english.encode("utf-8")).hexdigest()
        r={"source_hash":expected,"ko":"식인물고기",
           "source_dictionary":"test_en_ko.sst",
           "dictionary_record_index":5,"record":"CREA","field":"FULL",
           "form_id":"0xA","status":"imported"}
        a=normalized(r,"fallout4","sst","test.jsonl.gz")
        self.assertEqual(a[2],expected)
        self.assertEqual(a[11],"test_en_ko.sst#5")

    def test_kr9_korean_hash_is_not_english(self):
        r={"mod_version":"KR9","ko":"드웨머","record":"NPC_",
           "record_id":"Dwemer","field":"FNAM",
           "source_archive_member":"Morrowind_Korean_ReTranslation.esp",
           "subrecord_data_offset":127,
           "localized_subrecord_hash":"c"*64,"status":"imported"}
        a=normalized(r,"morrowind","kr9","test.jsonl")
        self.assertIsNone(a[2])
        self.assertIn("@127",a[11])

    def test_kr6_is_rejected(self):
        r={"mod_version":"KR6","ko":"드웨머","record":"NPC_",
           "record_id":"Dwemer","field":"FNAM",
           "source_archive_member":"old.esp",
           "subrecord_data_offset":127,"status":"imported"}
        with self.assertRaises(ValueError):
            normalized(r,"morrowind","kr9","test.jsonl")

    def test_same_string_id_different_table_is_distinct(self):
        a={"type":"string_table","deployed_path":"Strings/Fallout4_en.STRINGS",
           "string_id":224439}
        b={"type":"string_table","deployed_path":"Strings/Fallout4_en.DLSTRINGS",
           "string_id":224439}
        self.assertNotEqual(stable_identity(a,"fallout4","base"),
                            stable_identity(b,"fallout4","base"))

    def test_ui_duplicate_occurrences_are_distinct(self):
        a={"type":"translation_file","deployed_path":"Interface/Translate_en.txt",
           "key":"$Purchase Credits","occurrence":0}
        b={**a,"occurrence":1}
        self.assertNotEqual(stable_identity(a,"fallout4","base"),
                            stable_identity(b,"fallout4","base"))

    def test_missing_english_does_not_inherit_ko_hash(self):
        r={"game":"fallout4","content_language":"ko","ko":"식인물고기",
           "type":"string_table","deployed_path":"Strings/Fallout4_en.STRINGS",
           "string_id":1,"index":0,
           "source_ko_utf8_sha256":"a"*64,"source_file":"Data/Strings/Fallout4_en.STRINGS",
           "source_hash":"b"*64,"status":"extracted_unreviewed"}
        a=normalized(r,"fallout4","base","test.gz")
        self.assertIsNone(a[2])


if __name__=="__main__":
    unittest.main()
