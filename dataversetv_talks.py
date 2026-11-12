#!/usr/bin/env python3
"""Add DataverseTV talks that have slides.

Reads dataversetv.tsv (from a people.dataverse.org checkout, or the
DataverseTV spreadsheet exported as TSV) and writes dataversetv_talks.json:
every DataverseTV talk with a slides link that isn't already in the
inventory from OSF or the agendas. talks_from_raw.py adds them to talks.json.

Usage:
    python3 dataversetv_talks.py ~/github/gdcc/people.dataverse.org/data/dataversetv.tsv
    python3 talks_from_raw.py > talks.json

A DataverseTV talk counts as already listed when its slides are the same
OSF file, or when a listed talk is within 4 days and shares a speaker's
surname or has a very similar title.
"""

import csv
import difflib
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

from talks_from_raw import PROJECTS, SPEAKER_ALIASES, talks as osf_talks

# The "slides" for these are just the meeting agenda page; the talks in
# those sessions are already listed one by one from OSF.
AGENDA_PAGES = re.compile(r"projects\.iq\.harvard\.edu/dcm20\d\d/agenda")


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9 ]", "", s)


def surname(name):
    parts = norm(SPEAKER_ALIASES.get(name, name)).split()
    return parts[-1] if parts else ""


def osf_id(url):
    """The OSF ID of a single file. A link to a whole project doesn't count."""
    m = re.search(r"osf\.io/(?:download/)?([a-z0-9]{5})(?:[/?#]|$)", url or "")
    return m.group(1) if m and m.group(1) not in PROJECTS else None


def parse_date(s):
    try:
        return date.fromisoformat(s[:10])
    except ValueError:
        return None


def split_speakers(s):
    """'A (Org), B and C, et al.' -> ['A', 'B', 'C']"""
    s = re.sub(r"\([^)]*\)", "", s)
    names = []
    for part in re.split(r",| and ", s):
        part = re.sub(r"\s+", " ", re.sub(r"\bet al\.?", "", part)).strip(" .")
        if part:
            names.append(SPEAKER_ALIASES.get(part, part))
    return names


def already_listed(row, speakers, listed, by_osf):
    for url in row["slide_urls"]:
        if osf_id(url) in by_osf:
            return by_osf[osf_id(url)]
    when = parse_date(row["Date"])
    best, best_score = None, 0
    for t in listed:
        d = parse_date(t["date"])
        if not when or not d or abs((when - d).days) > 4:
            continue
        sim = difflib.SequenceMatcher(None, norm(row["Title"]), norm(t["title"])).ratio()
        shared = {surname(s) for s in speakers} & {surname(s) for s in t["speakers"]}
        if (shared and sim > 0.35) or sim > 0.75:
            score = sim + (0.5 if shared else 0)
            if score > best_score:
                best, best_score = t, score
    return best


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    listed = list(osf_talks()) + json.loads(Path("extra_talks.json").read_text())
    by_osf = {osf_id(t["slides"]): t for t in listed if osf_id(t.get("slides"))}

    out, skipped = [], []
    with open(Path(sys.argv[1]).expanduser(), newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            row = {k: (v or "").strip() for k, v in row.items() if k}
            urls = [row.get("Slides landing page", ""), row.get("Slides download URL", "")]
            row["slide_urls"] = [u for u in urls if u]
            if not row["slide_urls"]:
                continue
            speakers = split_speakers(row.get("Speakers", ""))
            if AGENDA_PAGES.search(row["slide_urls"][0]):
                skipped.append(f"{row['Date']} {row['Title']} (slides link is the agenda)")
                continue
            match = already_listed(row, speakers, listed, by_osf)
            if match:
                skipped.append(f"{row['Date']} {row['Title']} = {match['source']} {match['title']}")
                continue
            talk = {
                "date": row["Date"][:10],
                "title": re.sub(r'^Presentation slides "(.*)"', r"\1", row["Title"]),
                "speakers": speakers,
                "slides": row["slide_urls"][0],
                "source": "dataversetv",
                "type": "tutorial" if row.get("Type") == "tutorial" else "talk",
                "event": "",
                "date_from": "checked",
            }
            if row.get("Conference landing page"):
                talk["event_url"] = row["Conference landing page"]
            if row.get("YouTube ID"):
                talk["video"] = "https://www.youtube.com/watch?v=" + row["YouTube ID"]
            elif row.get("Non-YouTube landing page"):
                talk["video"] = row["Non-YouTube landing page"]
            out.append(talk)

    out.sort(key=lambda t: (t["date"], t["title"]))
    Path("dataversetv_talks.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(out)} new talks written to dataversetv_talks.json; "
          f"{len(skipped)} with slides were already listed or skipped:")
    for s in skipped:
        print("  " + s)


if __name__ == "__main__":
    main()
