"""Build readable records from official-master xTranslator Korean dictionaries.

No fuzzy matching or mod overrides. Preserve source field, index, English hash
and dictionary provenance; imported translations are not marked reviewed.
"""
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / 'docs/fallout/catalog.json'
PLUGINS = {
 'fo3': 'Fallout3 Anchorage ThePitt BrokenSteel PointLookout Zeta'.split(),
 'fnv': 'FalloutNV DeadMoney HonestHearts OldWorldBlues LonesomeRoad GunRunnersArsenal CaravanPack ClassicPack MercenaryPack TribalPack'.split(),
 'fo4': 'Fallout4 DLCRobot DLCworkshop01 DLCworkshop02 DLCworkshop03 DLCCoast DLCNukaWorld'.split(),
}

def main():
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    from group_fallout_terminals import expand, group
    records = [r for r in expand(catalog['entries']) if not r['id'].startswith('sst-')]
    groups = defaultdict(list)
    for game, plugins in PLUGINS.items():
        folder = 'Fallout4' if game == 'fo4' else 'FalloutNewVegas'
        wanted = {p.lower() + '_en_ko.sst': p + '.esm' for p in plugins}
        for path in sorted((ROOT / folder / 'Dictionaries').rglob('tm_*.jsonl.gz')):
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                for line in f:
                    r = json.loads(line)
                    plugin = wanted.get(r.get('source_dictionary', '').lower())
                    if plugin and r.get('record') in ('TERM', 'NOTE', 'BOOK'):
                        groups[game, plugin, r['record'], f"{int(r['form_id'],16):08X}"].append((r, str(path.relative_to(ROOT)).replace('\\','/')))
    lookup = defaultdict(list)
    for r in records:
        if r.get('plugin'):
            lookup[r['game'], r['plugin'].lower(), r['record_type'], r['form_id']].append(r)
    stats = Counter()
    for (game, plugin, record, form), rows in groups.items():
        byfield = defaultdict(dict)
        for r, path in rows:
            byfield[r['field']][r['sub_index']] = (r, path)
        title = byfield['FULL'].get(0, ({}, ''))[0].get('ko', '')
        targets = lookup[game, plugin.lower(), record, form]
        welcome_offset = 1 if any(t.get('field') == 'welcome-0' for t in targets) else 0
        bodyfields = ('BTXT', 'UNAM') if game == 'fo4' and record == 'TERM' else ('DESC', 'RNAM') if record == 'TERM' else ('TNAM',) if record == 'NOTE' else ('DESC',)
        for field in bodyfields:
            for index, (r, path) in byfield[field].items():
                body = r.get('ko', '').strip()
                if not re.search('[가-힣]', body) or '\ufffd' in body:
                    stats['rejected_text'] += 1
                    continue
                key = 'welcome-0' if field == 'DESC' and record == 'TERM' else f'menu-{index + welcome_offset}' if field == 'RNAM' else 'body'
                matches = [t for t in targets if t['field'] == key] if game != 'fo4' or record != 'TERM' else []
                if len(matches) == 1:
                    entry = matches[0]
                else:
                    entry = dict(id=f'sst-{game}-{plugin[:-4].lower()}-{record.lower()}-{form.lower()}-{field.lower()}-{index}', game=game, plugin=plugin, record_type=record, form_id=form, field=f'{field}:{index}', level='entry', type='terminal' if record == 'TERM' else 'note' if record == 'NOTE' else 'book', title_en='', description=f'{plugin} · {record} · FormID {form}', source_name='기존 한글 번역 사전', source_url='', verification='official_dictionary_record', usage_status='unknown')
                    records.append(entry)
                caption = byfield['ITXT'].get(index, ({}, ''))[0].get('ko', '') if field in ('RNAM', 'UNAM') else ''
                entry.update(body_ko=body, title_ko=caption or title or entry.get('title_ko') or entry.get('title_en') or f'{record} {form}', status='imported_translation')
                if record == 'TERM':
                    entry['terminal_title_ko'] = title
                entry['translation_source'] = dict(archive=path, dictionary=r['source_dictionary'], record_index=r['dictionary_record_index'], field=field, sub_index=index, source_hash=r['source_hash'], string_id=r.get('string_id'), review_status='unreviewed')
                stats[game] += 1
    from group_fallout_series import group_series
    catalog.update(entries=group_series(group(records))[0], updated='2026-10-28', policy='metadata_and_existing_korean_translations', provenance='Official-master ESM index, archived Korean dictionaries and EPUB originals')
    CATALOG.write_text(json.dumps(catalog, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    report = dict(linked_text_fields_by_game={g:stats[g] for g in PLUGINS}, total_korean_text_fields=sum(bool(r.get('body_ko')) for r in records), grouped_korean_readable_records=sum(bool(r.get('body_ko')) for r in catalog['entries']), rejected_text=stats['rejected_text'], matching='Official dictionary filename + record type + full FormID + field/sub-index. FO3/FNV menu index includes the extracted welcome entry. FO4 BTXT/UNAM use dedicated field IDs.', review_status='Existing translations; not newly reviewed or in-game tested')
    (CATALOG.parent / 'translation-link-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))

if __name__ == '__main__':
    main()
