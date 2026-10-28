"""Fallout 76 official string, record and grouping regressions."""
import json,re,struct,sys,tempfile,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from import_fallout76 import ba2_index,read_records,scene_actions,plain

class ImportTests(unittest.TestCase):
    def test_archive_member_index(self):
        name=b'strings/seventysix_ko.strings';payload=b'data'
        blob=struct.pack('<4sI4sIQ',b'BTDX',1,b'GNRL',1,64)+struct.pack('<I4sIIQIII',0,b'txt\0',0,0,60,0,4,0)+payload+struct.pack('<H',len(name))+name
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source.ba2';p.write_bytes(blob)
            self.assertEqual(ba2_index(p)[name.decode()],(60,0,4))
    def test_info_parent_and_compression(self):
        fields=b'NAM1'+struct.pack('<H',4)+struct.pack('<I',123)
        payload=struct.pack('<I',len(fields))+zlib.compress(fields)
        record=struct.pack('<4s5I',b'INFO',len(payload),0x40000,42,0,0)+payload
        group=struct.pack('<4s5I',b'GRUP',24+len(record),99,7,0,0)+record
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'source.esm';p.write_bytes(group)
            raw,parents=read_records(p)
            self.assertEqual(parents[42],99)
            self.assertEqual(raw[42],('INFO',[('NAM1',struct.pack('<I',123))]))
    def test_scene_actions_follow_phase_and_do_not_read_timer_as_dialogue(self):
        u=lambda n:n.to_bytes(4,'little')
        fs=[('ANAM',b'\0\0'),('SNAM',u(2)),('INAM',u(1)),('DATA',u(100)),('ANAM',b''),('ANAM',b'\2\0'),('DATA',u(999)),('ANAM',b''),('ANAM',b'\0\0'),('SNAM',u(0)),('INAM',u(2)),('DATA',u(101)),('ANAM',b'')]
        self.assertEqual([topic for a in scene_actions(fs) for topic in a['topics']],[101,100])
        self.assertEqual(plain('<font color="#fff">본문<br>둘째 줄</font> <Alias=Player>'),'본문\n둘째 줄 <Alias=Player>')
    def test_published_official_records(self):
        folder=ROOT/'docs/fallout'
        rows=[r for r in json.loads((folder/'catalog.json').read_text(encoding='utf-8'))['entries'] if r['game']=='fo76']
        report=json.loads((folder/'fo76-import-report.json').read_text(encoding='utf-8'))
        self.assertEqual(len(rows),report['published_records'])
        self.assertGreater(len(rows),2900)
        self.assertEqual(report['missing_localized_string_ids'],{})
        for r in rows:
            with self.subTest(id=r['id']):
                self.assertTrue(r['official_localization'])
                self.assertEqual(r['body_version'],'official_game_localization')
                self.assertTrue(re.search('[가-힣]',r['body_ko']) or r.get('language_neutral_payload'))
                self.assertNotIn('\ufffd',r['body_ko'])
                self.assertTrue(r['translation_sources'])
                self.assertFalse(re.match(r'(?:zzz|cut[_-]|test|debug|dummy|unused|delete|deprecated)',r.get('editor_id',''),re.I))
                for src in r['translation_sources']:
                    self.assertEqual(src['translation_origin'],'official_ko')
                    self.assertGreater(src['string_id'],0)
                    self.assertEqual(len(src['korean_sha256']),64)
                if r['type']=='terminal':
                    self.assertGreater(r['terminal_page_count'],0)
                    self.assertTrue({s['form_id'] for s in r['translation_sources']}<=set(r['terminal_record_ids']))
                if r.get('series_member_count'):
                    self.assertEqual(len(r['reference_series_members']),r['series_member_count'])
                    self.assertFalse(r.get('series_entries'))
        overseer=next(r for r in rows if r['title_en']=="Overseer's Log" and r['type']=='holotape')
        self.assertEqual(overseer['series_member_count'],18)
        survivor=next(r for r in rows if r['title_en']=='Survivor Story')
        self.assertEqual(survivor['series_member_count'],10)
        code=next(r for r in rows if r['id']=='fo76-book-0041b8d2')
        self.assertEqual(code['body_ko'],'851')
        voice=next(r for r in rows if r['id']=='fo76-note-0090f5a3')
        self.assertTrue(voice['transcript_sections'])
        self.assertTrue(all(s['field']=='NAM1' for s in voice['translation_sources']))

if __name__=='__main__':unittest.main()
