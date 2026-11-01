# Oblivion.esm verified English source (2026-11-01)

User-supplied original `Oblivion.esm` (277,504,985 bytes; SHA-256 `a26e21ea8c3041f8737ffb3a266129dedb7f8a88590625ecfecd5eb7f66b4a70`) was parsed without record or decompression errors.

- 1,167,017 source records; 41,789 compressed records.
- 46,963 extracted English text fields, split into eight JSONL source files.
- **46,225 / 46,225 existing BaseGame canonical translations:** identical plugin/record/FormID/field/sub_index **and** identical SHA-256 of English text.
- **0** translation rows missing from source; **0** English SHA mismatches.
- **738** source-only English fields are not represented in the existing Korean translation memory. Keep these separate from approved translations.
- Shivering Isles records reside in this `Oblivion.esm`; the `DLCShiveringIsles.esp` supplied alongside the game is only an 85-byte master-reference stub.

The original Korean `canonical_v2.jsonl` is intentionally left intact in this draft. The eight `oblivion_esm_en.part-NN.jsonl` files are normalized **English source sidecars**, keyed by `plugin, record, form_id, field, sub_index`. For each source record `source_hash = SHA256(source_en UTF-8)`.

Validate the sidecars against the existing Korean records:

```bash
python tools/verify_oblivion_esm_english.py
```

To generate an **untracked copy** of the canonicals with `source_en` attached, and a separate English-only candidate file:

```bash
python tools/verify_oblivion_esm_english.py --write-merged work/oblivion_esm_enriched.jsonl --write-unpaired work/oblivion_esm_unpaired_en.jsonl
```

The script checks every source part's SHA-256 and byte size against `source_manifest.json`, verifies each record's English hash, and refuses to overwrite the canonical original or an existing output.

**Publication caveat:** These sidecars contain original game writing and are only on a draft review branch. The archive previously kept original text hashes without full English game text; check copyright/republication permission and archive policy before merging or publishing them from a public repository.

No engine files, Korean translations, translation statuses, or game installations were changed.
