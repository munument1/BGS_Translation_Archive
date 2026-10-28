"""Publication regressions: empty entries, mixed taxonomy and false completion."""
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def main():
    entries=json.loads((ROOT/'docs/fallout/catalog.json').read_text(encoding='utf-8'))['entries']
    assert len(entries)==len({r['id'] for r in entries}), 'Duplicate IDs'
    for r in entries:
        assert r['type'] in ('terminal','holotape','document'),r['id']
        assert (r.get('body_ko') or '').strip() or (r.get('body_en') or '').strip(),r['id']
        assert (r.get('body_ko') or '').strip(),('Korean body is not linked',r['id'])
        assert r.get('status')!='partial_translation',('Incomplete archival link',r['id'])
        if r.get('translation_coverage',{}).get('complete'):
            assert '[미번역 원문]' not in r.get('body_ko',''),r['id']
        if '[미번역 원문]' in (r.get('body_ko') or ''):
            assert r['status']=='partial_translation',r['id']
        if r['status']=='partial_translation':
            assert not r.get('translation_coverage',{}).get('complete'),r['id']
    keller=next(r for r in entries if r.get('title_en')=='Keller Family Transcript')
    eddie=next(r for r in entries if r.get('title_en')=='Eddie Winter Holotapes')
    for r in (keller,eddie):
        assert r['type']=='holotape' and r['translation_coverage']['complete']
        assert r['body_ko'] and r['body_en']
    lorenzo=next(r for r in entries if r.get('title_en')=='Lorenzo Cabot’s journal')
    assert lorenzo['translation_coverage']['complete'] and len(lorenzo['body_ko'])>1000
    assert '<font' not in lorenzo['body_ko'].lower()
    targets=json.loads((ROOT/'docs/fallout/completion-targets.json').read_text(encoding='utf-8'))
    resolved={i for r in entries for i in (r['id'],*r.get('aliases',[]))}
    assert len(targets['target_ids'])==570
    assert set(targets['target_ids'])-resolved==set(targets['excluded_ids'])
    voice=next(r for r in entries if r['id']=='codex-907071b3f7f4fab4')
    assert voice['translation_coverage']['resolved_fields']==3
    assert voice['canonical_record_links'][0]['dialogue_form_id']=='09007D94'
    assert voice['body_version']=='existing_game_translation'
    for r in entries:
        if r.get('canonical_record_links'):
            assert not r.get('series_entries'),('Stale partial series snapshot',r['id'])
    cappy=next(r for r in entries if r['id']=='codex-210b550f558d48c6')
    assert cappy['language_neutral_payload']
    assert [s for s in cappy['body_ko'].splitlines() if len(s)==1]==list('GRENFIEHRS')
    print(f'PASS: {len(entries)} readable entries; three categories; honest translation states; Keller/Eddie transcripts complete')

if __name__=='__main__':main()
