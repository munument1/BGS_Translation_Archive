#!/usr/bin/env python3
"""Verify original-English sidecars against canonical Oblivion translations.

Default is validation-only. This never overwrites a canonical translation file.
For a merged export, use --write-merged <new-output.jsonl>.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCHIVE = ROOT / 'Oblivion/BaseGame/Oblivion.esm/canonical_v2.jsonl'
DEFAULT_SOURCE_DIR = ROOT / 'Oblivion/BaseGame/Oblivion.esm/english_source'
DEFAULT_MANIFEST = DEFAULT_SOURCE_DIR / 'source_manifest.json'


def ident(r):
    return (str(r['plugin']).casefold(), str(r['record']), str(r['form_id']).upper(),
            str(r['field']), int(r.get('sub_index') or 0))


def sha_text(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def read_jsonl(path):
    with path.open(encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            if line.strip():
                try: yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f'Invalid JSON: {path}:{line_no}') from exc


def reconcile(archive, source_dir, manifest, output=None, unpaired_output=None,
              expected_canonical=46225, expected_source=46963, expected_unpaired=738):
    files = manifest['source_parts']
    found = {}
    for part in files:
        path = source_dir / Path(part['path']).name
        if not path.is_file(): raise FileNotFoundError(path)
        with path.open('rb') as f: sha = hashlib.file_digest(f,'sha256').hexdigest()
        if sha != part['sha256']: raise ValueError(f'Source part SHA mismatch: {path}')
        if path.stat().st_size != part['bytes']: raise ValueError(f'Source part size mismatch: {path}')
        n = 0
        for row in read_jsonl(path):
            n += 1
            if row.get('plugin') != 'Oblivion.esm': raise ValueError(f'Wrong plugin {path}')
            if sha_text(row['source_en']) != row['source_hash']:
                raise ValueError(f'Source English hash mismatch: {ident(row)}')
            k = ident(row)
            if k in found: raise ValueError(f'Duplicate source identity: {k}')
            found[k] = row
        if n != part['rows']: raise ValueError(f'Part row count mismatch: {path} ({n})')
    if len(found) != expected_source: raise ValueError(f'Unexpected source count: {len(found)}')

    if output is not None:
        output = Path(output)
        if output.resolve() == archive.resolve():
            raise ValueError('Refusing to overwrite canonical archive')
        if output.exists(): raise FileExistsError(f'Output exists: {output}')
        output.parent.mkdir(parents=True,exist_ok=True)
    if unpaired_output is not None:
        unpaired_output = Path(unpaired_output)
        if unpaired_output.exists(): raise FileExistsError(f'Output exists: {unpaired_output}')
        unpaired_output.parent.mkdir(parents=True,exist_ok=True)

    seen = set()
    canonical_count = matches = 0
    # Only write a new merged artifact after the entire source is validated.
    merged = []
    for row in read_jsonl(archive):
        canonical_count += 1
        k = ident(row)
        if k in seen: raise ValueError(f'Duplicate canonical identity: {k}')
        source = found.get(k)
        if source is None: raise ValueError(f'Missing source record: {k}')
        if row['source_hash'] != source['source_hash']:
            raise ValueError(f'English source hash conflict: {k}')
        seen.add(k)
        matches += 1
        if output is not None:
            combined = dict(row)
            if 'source_en' in combined and combined['source_en'] != source['source_en']:
                raise ValueError(f'Prior source_en differs: {k}')
            combined['source_en'] = source['source_en']
            merged.append(combined)

    extras = [row for key,row in found.items() if key not in seen]
    if (canonical_count, matches, len(extras)) != (expected_canonical, expected_canonical, expected_unpaired):
        raise ValueError(f'Unexpected counts: canonical={canonical_count} matched={matches} extra={len(extras)}')
    if output is not None:
        with output.open('w',encoding='utf-8',newline='\n') as f:
            for row in merged: f.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
    if unpaired_output is not None:
        with unpaired_output.open('w',encoding='utf-8',newline='\n') as f:
            for row in extras: f.write(json.dumps(row,ensure_ascii=False,separators=(',',':'))+'\n')
    return {'canonical_records':canonical_count,'source_records':len(found),
            'verified_matches':matches,'hash_conflicts':0,'unpaired_english_candidates':len(extras),
            'merged_export':str(output) if output else None,
            'unpaired_export':str(unpaired_output) if unpaired_output else None}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,default=DEFAULT_ARCHIVE)
    p.add_argument('--source-dir',type=Path,default=DEFAULT_SOURCE_DIR)
    p.add_argument('--manifest',type=Path,default=DEFAULT_MANIFEST)
    p.add_argument('--write-merged',type=Path,default=None)
    p.add_argument('--write-unpaired',type=Path,default=None)
    p.add_argument('--expected-canonical',type=int,default=46225)
    p.add_argument('--expected-source',type=int,default=46963)
    p.add_argument('--expected-unpaired',type=int,default=738)
    args=p.parse_args()
    meta=json.loads(args.manifest.read_text(encoding='utf-8'))
    result=reconcile(args.archive,args.source_dir,meta,args.write_merged,args.write_unpaired,
                    args.expected_canonical,args.expected_source,args.expected_unpaired)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
