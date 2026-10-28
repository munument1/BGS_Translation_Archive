"""Export a bounded, review-only queue of ambiguous English-hash translations.

Never auto-select a Korean variant. Exact source hash equality does NOT mean
two contexts need the same wording (titles, NPC address, UI, grammatical
particles and register can differ). This tool does not expose English text.

    python tools/export_conflict_review.py --limit 150
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import sqlite3

ROOT=Path(__file__).resolve().parents[1]
DEFAULT_DB=ROOT/"work/translation_memory.sqlite3"
DEFAULT_OUT=ROOT/"dictionaries/analysis/conflicts_to_review.jsonl"


def run(db,out,limit):
    if not 1<=limit<=1000:
        raise ValueError("Limit must be 1..1000")
    if not db.is_file():
        raise FileNotFoundError(f"Build local DB first: {db}")
    con=sqlite3.connect(f"file:{db.as_posix()}?mode=ro",uri=True)
    try:
        # Only hash keys backed by actual English source text; do not mix
        # Korean-only KR9/BaseGame rows with English original SHA identifiers.
        records=con.execute("""
            SELECT english_sha, COUNT(*) AS occurrence_count,
                   COUNT(DISTINCT ko) AS translation_variant_count,
                   COUNT(DISTINCT game) AS game_count
            FROM entry
            WHERE english_sha IS NOT NULL
            GROUP BY english_sha
            HAVING COUNT(DISTINCT ko)>1
            ORDER BY occurrence_count DESC, english_sha ASC
            LIMIT ?
        """,(limit,)).fetchall()
        out.parent.mkdir(parents=True,exist_ok=True)
        with out.open("w",encoding="utf-8",newline="\n") as f:
            for source_sha,occ,variants,games in records:
                rows=con.execute("""
                    SELECT game, dataset, ko, source_dictionary, record_type, field,
                           COUNT(*) occurrences
                    FROM entry WHERE english_sha=?
                    GROUP BY game,dataset,ko,source_dictionary,record_type,field
                    ORDER BY occurrences DESC, game, ko LIMIT 120
                """,(source_sha,)).fetchall()
                seen=defaultdict(lambda:{"rows":0,"games":set(),"contexts":[]})
                for game,kind,ko,source_dict,record,field,count in rows:
                    group=seen[ko]
                    group["rows"]+=count
                    group["games"].add(game)
                    if len(group["contexts"])<4:
                        group["contexts"].append({
                            "game":game,"dataset":kind,"dictionary":source_dict,
                            "record":record,"field":field,"rows":count})
                result={
                    "english_sha256":source_sha,
                    "total_occurrences":occ,
                    "korean_variant_count":variants,
                    "games_observed":games,
                    "preview_limit":120,
                    "variants":[
                        {"ko_excerpt":ko[:160],"ko_length":len(ko),
                         "rows_in_preview":v["rows"],
                         "games":sorted(v["games"]),
                         "example_contexts":v["contexts"]}
                        for ko,v in sorted(seen.items(),key=lambda x:(-x[1]["rows"],x[0]))
                    ],
                    "review_status":"manual_context_review_required",
                    "chosen_korean":None,
                    "notes":"Do not infer a winner by popularity or apply across plugin contexts."
                }
                f.write(json.dumps(result,ensure_ascii=False,separators=(",",":"))+"\n")
        print(f"PASS wrote {len(records)} ranked ambiguity groups to {out}",flush=True)
    finally:
        con.close()


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db",type=Path,default=DEFAULT_DB)
    ap.add_argument("--output",type=Path,default=DEFAULT_OUT)
    ap.add_argument("--limit",type=int,default=150)
    args=ap.parse_args()
    run(args.db,args.output,args.limit)
