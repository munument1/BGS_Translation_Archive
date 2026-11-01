# Skyrim book translation refresh — 2026-11-01

## Order of operations

1. Refresh Tamriel Library Skyrim BOOK translations.
2. Extract original English text using the user's locally owned Skyrim ESM/ESL files and English STRINGS, then associate English/Korean by plugin + FormID + record + field + string ID and hashes.
3. Normalize Skyrim translations in the BGS Translation Archive.
4. Compare terminology with Morrowind KR12.4, Oblivion v1.2.0, Daggerfall, and other Elder Scrolls games.

Do **not** begin cross-game terminology replacements before English/Korean mapping is verified.

## Current evidence

- Published archive: **977** Skyrim BOOK records, in sources/skyrim_books/.
- Translation source: https://github.com/servaltullius/Skyrim_Translator_v6
- Source pinned for candidate extraction: dc1796e26f5b3d1db0e1116c5a0b04a13759dba9 (2026-11-01).
- The upstream package documentation describes its Korean patch as **Skyrim AE(SE) 26.10.16 beta 6** and reports a review of 1,032 books. This is not proof that 55 books are missing from our archive; collection scope and record identity must be compared.
- Korean STRINGS file IDs alone cannot identify BOOK FormIDs. The user's original game ESM/ESL plugins are indispensable for lossless remapping.
- The game originals must **not** be uploaded to the public GitHub repository.

## Candidate generation (Windows PowerShell)

From the archive working tree, clone the upstream patch beside it and check out the pinned revision:

    git clone https://github.com/servaltullius/Skyrim_Translator_v6.git ..\Skyrim_Translator_v6
    git -C ..\Skyrim_Translator_v6 checkout dc1796e26f5b3d1db0e1116c5a0b04a13759dba9

Use the *actual* Skyrim Data directory in place of the sample path:

    python tools/refresh_skyrim_book_translation.py --patch-root "..\Skyrim_Translator_v6\Skyrim_Latest_Kor\01-main" --plugins-dir "D:\SteamLibrary\steamapps\common\Skyrim Special Edition\Data" --source-revision dc1796e26f5b3d1db0e1116c5a0b04a13759dba9 --output ".local\skyrim-book-refresh"

Read the generated report at .local/skyrim-book-refresh/review_report.json.

The generated candidate source files are in .local/skyrim-book-refresh/sources_skyrim_books/.
The script deliberately leaves the published source files, all games, and website unchanged. It preserves unmatched originals, rejects duplicate record keys, and holds changed EditorIDs or runtime substitution tags for review.

After manual review, update the existing source shards and let the existing build-book-collection.yml workflow regenerate the Skyrim individual books, anthology, indexes, and search data. Validate book identity, count, source attribution, dynamic tags, and unchanged Morrowind/Oblivion/Daggerfall counts before publication.

## Rights and provenance

The upstream Readme credits the Elder Scrolls gallery Korean patch and describes that original patch as freely modifiable/distributable. Keep the provenance and attribution of all participating translators and confirm applicable terms before publishing the new version. Do not upload proprietary game binaries or the full English game text.

**Status:** importer and tests prepared for review; no book replacement or website deployment yet because original game plugins are inaccessible.
