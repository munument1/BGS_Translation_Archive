#!/usr/bin/env python3
"""Export imported books through the existing anthology/Markdown formatter."""
from collections import defaultdict
import json
from pathlib import Path

from build_book_collection import export

LABELS = {'battlespire':'Battlespire', 'redguard':'Redguard', 'shadowkey':'Shadowkey',
          'eso':'Online', 'eso_journals':'Online Journals, Notes & Letters'}

def build(root):
    root = Path(root).resolve()
    folder = root/'docs/books'
    data = json.loads((folder/'external_english_texts.json').read_text(encoding='utf-8'))
    previews = json.loads((folder/'external_korean_previews.json').read_text(encoding='utf-8'))
    korean = json.loads((folder/'external_korean_texts.json').read_text(encoding='utf-8'))
    titles = {x['uid']:x['title_ko'] for x in previews['entries'] if x.get('uid') and x.get('title_ko')}
    translations = {x['uid']:x for x in korean['entries'] if x.get('coverage')=='full' and x.get('body_ko')}
    new_korean = json.loads((folder/'external_korean_translations.json').read_text(encoding='utf-8'))
    review = new_korean.get('review', {})
    reviewed_uids = set(review.get('reviewed_uids', []))
    unresolved = review.get('unresolved', {})
    for item in new_korean['entries']:
        if item['uid'] in translations:
            raise ValueError('Existing full Korean translation must be preserved: '+item['uid'])
        if item.get('coverage')!='available_source_text' or not item.get('body_ko'):
            raise ValueError('Expected a translation of available source text: '+item['uid'])
        translations[item['uid']] = item
    groups = defaultdict(list)
    for item in data['entries']:
        if item['game'] not in LABELS:
            raise ValueError('Unexpected game: '+item['game'])
        translated = translations.get(item['uid'])
        row = dict(game=item['game'], book_id=item['uid'], record='BOOK', field='DESC',
                   title_en=item['title_en'], title_ko=titles.get(item['uid'], ''),
                   en=item['body_en'], source_language='en', content_language='en',
                   status='untranslated', source_ref=item['source_url'],
                   source_sha256=item['source_sha256'], source_notes_en=item.get('source_notes_en',''),
                   needs_source_review=True)
        if translated:
            row.update(title_ko=translated['title_ko'],ko=translated['body_ko'],content_language='ko',status='translated')
            if translated.get('coverage')=='available_source_text':
                if translated.get('source_sha256')!=item['source_sha256']:
                    raise ValueError('Translation source has changed: '+item['uid'])
                row.update(translation_coverage=translated['coverage'],
                           needs_translation_review=translated.get('needs_translation_review',True),
                           translation_notes=translated.get('translation_notes',''))
                if item['uid'] in reviewed_uids:
                    row.update(translation_review='needs_source_check' if item['uid'] in unresolved else 'source_compared',
                               review_method=review['method'],review_notes=unresolved.get(item['uid'],''))
        groups[item['game']].append(row)
    catalog, fulltext, results = [], [], []
    for game,label in LABELS.items():
        # Restrict the existing exporter's generated-file cleanup to these known shelves.
        target = (folder/game/'books').resolve()
        if not target.is_relative_to(folder.resolve()):
            raise ValueError('Export outside docs/books')
        results.append(export(folder,game,groups[game],language_label='원문·번역',game_label=label,
                              source_note='영문 원문을 우선 수록했습니다. 미번역 서적의 판본·발췌 여부는 번역 전에 확인하세요.'))
        for row in groups[game]:
            body = row.get('ko') or row['en']
            catalog.append(dict(uid=row['book_id'],game=game,title=row['title_ko'] or row['title_en'],
                                title_en=row['title_en'],author='',plugin='',record_id=row['book_id'],
                                path=game+'/'+row['file_path'],source=row['source_ref'],
                                preview=' '.join(body.split())[:185],length=len(body),
                                content_language=row['content_language'],translation_status=row['status']))
            if row.get('translation_coverage')=='available_source_text':
                catalog[-1].update(translation_coverage=row['translation_coverage'],
                                   needs_translation_review=row['needs_translation_review'])
                if row.get('translation_review'):
                    catalog[-1].update(translation_review=row['translation_review'],
                                       review_method=row['review_method'],review_notes=row['review_notes'])
            fulltext.append(dict(uid=row['book_id'],text=body))
    (folder/'additional_catalog.json').write_text(json.dumps(dict(schema_version=1,books=catalog,
        counts={g:len(groups[g]) for g in LABELS}),ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (folder/'additional_fulltext-index.json').write_text(json.dumps(fulltext,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (folder/'additional_manifest.json').write_text(json.dumps(dict(schema_version=1,games=results),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    readme=folder/'README.md'
    text=readme.read_text(encoding='utf-8').split('\n## 외전과 온라인 서적\n')[0]
    text=text.replace('영어 서적 본문 전문은 포함하지 않습니다.','추가 게임의 영문 원문은 아래 외전과 온라인 서가에 수록합니다.')
    lines=['','## 외전과 온라인 서적','','기존 시리즈와 동일한 개별 Markdown·전체 합본·40권 분할본·JSONL 양식입니다. 미번역 서적은 영문으로 수록했습니다.','',
           '| 게임 | 수록 | 열람 |','|---|---:|---|']
    for game,label in LABELS.items():
        lines.append(f'| {label} | {len(groups[game]):,}권 | [열기]({game}/index.md) |')
    lines.extend(['','[수록 현황 및 남은 항목](ENGLISH_SOURCES.md) · [웹 서가](../index.html)',''])
    readme.write_text(text.rstrip()+'\n'+'\n'.join(lines),encoding='utf-8')
    return dict(books=len(catalog),games={g:len(groups[g]) for g in LABELS})

if __name__=='__main__':
    print(json.dumps(build(Path(__file__).resolve().parents[1]),ensure_ascii=False))
