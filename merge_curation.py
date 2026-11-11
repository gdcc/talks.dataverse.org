#!/usr/bin/env python3
"""Merge agenda-matching results (JSON arrays) into curation.json.

Usage:
    python3 merge_curation.py results/*.json

Each input record needs `source` and `file_path`; later inputs win.
"""
import json
import sys
from pathlib import Path

KEEP = ("source", "file_path", "title", "speakers", "date", "event",
        "confidence", "evidence", "notes")

path = Path("curation.json")
cur = {(c["source"], c["file_path"]): c for c in json.loads(path.read_text())} if path.exists() else {}
for f in sys.argv[1:]:
    for r in json.loads(Path(f).read_text()):
        cur[(r["source"], r["file_path"])] = {k: r[k] for k in KEEP if k in r}
out = sorted(cur.values(), key=lambda c: (c["source"], c["file_path"]))
path.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
print(f"{len(out)} entries in {path}")
