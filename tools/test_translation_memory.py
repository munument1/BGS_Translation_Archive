"""Boundary tests: never confuse English hashes or merge distinct table IDs.

Run from repo root: python -m unittest discover -s tools -p test_translation_memory.py
"""
import hashlib
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from translation_memory import lookup, normalized, stable_identity


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

    def test_lookup_escaping_and_exact_filter_scope(self):
        with tempfile.TemporaryDirectory() as tmp:
            db=Path(tmp)/"test.sqlite3"
            connection=sqlite3.connect(db)
            connection.execute(
                "CREATE TABLE entry (game TEXT, dataset TEXT,english_sha TEXT,ko TEXT,"
                "source_file TEXT,source_dictionary TEXT,record_type TEXT,field TEXT,"
                "record_id TEXT,plugin TEXT,ordinal INTEGER,identity TEXT,status TEXT)"
            )
            en=hashlib.sha256(b"Slaughterfish").hexdigest()
            connection.executemany(
                "INSERT INTO entry VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",[
                    ("morrowind","kr9",None,"저장\\경로","KR9","KR9","MGEF","DESC","",
                     "OpenMW_KR9",1,"kr9@1","imported"),
                    ("morrowind","kr9",None,"ABC_% 문장","KR9","KR9","MGEF","DESC","",
                     "OpenMW_KR9",2,"kr9@2","imported"),
                    ("oblivion","oblivion",en,"식인물고기","Oblivion","canonical","CREA",
                     "FULL","0001","Oblivion.esm",0,"ob1","imported")
                ])
            connection.commit()
            connection.close()

            def query(**kwargs):
                output=io.StringIO()
                defaults={"english":None,"korean":None,"record_id":None,"game":None,
                          "limit":20,"full":False}
                defaults.update(kwargs)
                with redirect_stdout(output):
                    lookup(db,**defaults)
                return json.loads(output.getvalue())

            self.assertEqual(query(korean="\\",game="morrowind")["total_hits"],1)
            self.assertEqual(query(korean="_%",game="morrowind")["total_hits"],1)
            self.assertEqual(query(record_id="",game="morrowind",record_type="MGEF")["total_hits"],2)
            self.assertEqual(query(english="Slaughterfish",game="oblivion")["same_english_korean_variants"],1)
            no_hits=query(english="Slaughterfish",game="oblivion",record_id="0002")
            self.assertEqual(no_hits["total_hits"],0)
            self.assertEqual(no_hits["same_english_korean_variants"],0)
            identity=query(identity="kr9@1",game="morrowind")
            self.assertEqual(identity["returned"],1)
            self.assertEqual(identity["entries"][0]["identity"],"kr9@1")


if __name__=="__main__":
    unittest.main()
