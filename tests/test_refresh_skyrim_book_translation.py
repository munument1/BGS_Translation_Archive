import sys
from pathlib import Path
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from refresh_skyrim_book_translation import key,load,prepare,write_shards

REV="dc1796e26f5b3d1db0e1116c5a0b04a13759dba9"

def row(fid,text,edid="book"):
    return {"plugin":"Skyrim.esm","form_id":fid,"book_id":fid,"editor_id":edid,"ko":text,"title_ko":"책","record":"BOOK","field":"DESC"}

class RefreshTests(unittest.TestCase):
    def test_identity_and_unmatched_preserved(self):
        a=row("0001","옛"),b=row("0002","유지"),c=row("0003","추가")
        out,report=prepare({key(a):a,key(b):b},[row("0001","새"),c],REV)
        self.assertEqual(len(out),3)
        self.assertEqual(report["counts"]["changed"],1)
        self.assertEqual(report["counts"]["new"],1)
        self.assertEqual(report["counts"]["preserved_unmatched"],1)
    def test_unsafe_held(self):
        a=row("0001","<Global=Count>개",edid="a")
        b=row("0001","<Global=Other>개",edid="a")
        out,report=prepare({key(a):a},[b],REV)
        self.assertEqual(out[0]["ko"],a["ko"])
        self.assertEqual(report["counts"]["held"],1)
    def test_shards_and_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)
            write_shards([row("0001","가"),row("0002","나")],path)
            self.assertEqual(len(load(path)),2)
            with (path/"skyrim_books_999.jsonl").open("w",encoding="utf8") as f:
                import json
                f.write(json.dumps(row("0001","다"),ensure_ascii=False)+"\n")
            with self.assertRaisesRegex(ValueError,"Duplicate"):load(path)
    def test_revision_required(self):
        with self.assertRaisesRegex(ValueError,"SHA"):prepare({},[],"main")

if __name__=="__main__":unittest.main()
