#!/usr/bin/env python3
"""List the talks that aren't shown on the website because they have no slides.

They're still in talks.json, with "slides": null. To show one, add a link to
its slides where the talk comes from (printed for each talk) and regenerate
talks.json:

    python3 talks_from_raw.py > talks.json

Usage:
    python3 hidden_talks.py
"""

import json
from collections import defaultdict
from pathlib import Path

WHERE = {
    "agenda": "extra_talks.json: set \"slides\"",
    "dataversetv": "the DataverseTV spreadsheet: fill in \"Slides landing page\", "
                   "then rerun dataversetv_talks.py",
}


def main():
    talks = json.loads(Path("talks.json").read_text())
    hidden = [t for t in talks if not t.get("slides")]
    by_year = defaultdict(list)
    for t in hidden:
        by_year[t["date"][:4]].append(t)

    print(f"{len(hidden)} of {len(talks)} talks have no slides and are hidden on the website.\n")
    for year in sorted(by_year):
        print(f"{year} ({len(by_year[year])})")
        for t in sorted(by_year[year], key=lambda t: (t["date"], t["title"])):
            kind = "" if t.get("type", "talk") == "talk" else f" [{t['type']}]"
            speakers = ", ".join(t["speakers"]) or "no speakers listed"
            print(f"  {t['date']}  {t['title']}{kind}")
            print(f"              {speakers}")
        print()

    print("To show a talk, add its slides link in:")
    for source in sorted({t["source"].split(":")[0] for t in hidden}):
        print(f"  {source}: {WHERE.get(source, 'the source it came from')}")


if __name__ == "__main__":
    main()
