#!/usr/bin/env python3
"""Turn raw OSF file records (from osf_inventory.py) into a list of talks.

Reads raw/<osf-id>.json for each project in PROJECTS and prints talks.json.
Uses only the Python standard library.

Usage:
    python3 talks_from_raw.py > talks.json

Titles are cleaned-up file names and are a first draft. Speakers are left
empty: OSF only tells us who uploaded the files, not who gave the talk.
"""

import json
import re
import sys
from pathlib import Path

# OSF project ID -> (event name, first day of the event).
# The first day is used when a file's own date can't be worked out.
PROJECTS = {
    "3xcq8": ("Dataverse Community Meeting 2017", "2017-06-14"),
    "e5n3h": ("Dataverse Community Meeting 2017", "2017-06-14"),
    "ke9gc": ("Open Repositories 2018", "2018-06-04"),
    "h8yjw": ("Dataverse Community Meeting 2019", "2019-06-19"),
    "prq46": ("Dataverse Community Meeting 2020", "2020-06-17"),
    "gav6m": ("Dataverse Community Meeting 2021", "2021-06-14"),
    "fqmwb": ("Dataverse Community Meeting 2022", "2022-06-14"),
    "5k47u": ("Dataverse Community Meeting 2023", "2023-06-05"),
    "95ycg": ("Dataverse Community Meeting 2024", "2024-03-04"),
    "j4r2e": ("Dataverse Community Meeting 2025", "2025-06-10"),
    "awbjp": ("Dataverse Community Meeting 2026", "2026-05-12"),
    "wpixk": ("BITSS 2014 Summer Institute", "2014-06-02"),
}

# Files that hold slides. Everything else (recordings, photos, notes) is skipped.
SLIDE_EXTENSIONS = {"pdf", "pptx", "ppt", "key", "odp", "html"}

# Files in these projects that aren't Dataverse talks (papers, flyers, agendas).
SKIP_FILES = {
    ("wpixk", "/The_Evolution_of_Data_Citation.pdf"),
    ("wpixk", "/Toward_A_Common_Framework_for_Statistical_Analysis_and_Development.pdf"),
    ("wpixk", "/A_Data_Sharing_Story.pdf"),
    ("wpixk", "/Replication_Replication.pdf"),
    ("wpixk", "/Ten_Simple_Rules_for_the_Care_and_Feeding_of_Scientific_Data.pdf"),
    ("e5n3h", "/OSF-Definitions.pptx"),
    ("j4r2e", "/DCM2025Agenda_PresentationChecklist.pdf"),
    ("ke9gc", "/Using Dataverse across the Globe.pdf"),  # panel proposal
    ("95ycg", "/March 6, Wednesday/9-30-Snapp-bio.pdf"),  # speaker bio
    # Duplicate uploads of the same talk; the other copy is kept.
    ("awbjp", "/DCM2026 - Fairvault -ThomasThomas.pdf"),
    ("awbjp", "/Dataverse Community Meeting 2026.pdf"),
    ("j4r2e", "/Jun10 - Tuesday Workshops/1515 - 2025DCM_GREI UPDATES_SoniaBarbosa.pdf"),
    ("j4r2e", "/Jun12 - Thursday/1530 - Data Repository Track - Plankyte_DV2025.pdf"),
}

MONTHS = {m: i for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}


def file_date(path, event_start):
    """Return (date, how) for a file, using its name or folder if possible."""
    year = event_start[:4]
    # 2019-06-19-Name-Title.pdf, Folder_(2020-06-18), 2023-06-05_...
    m = re.search(r"(20\d\d)-(\d\d)-(\d\d)", path)
    if m and m.group(1) == year:
        return m.group(0), "file"
    # 06152017-Name-Title.pdf (2017)
    m = re.search(r"/(\d\d)(\d\d)(20\d\d)-", path)
    if m and m.group(3) == year:
        return f"{year}-{m.group(1)}-{m.group(2)}", "file"
    folder = path.rsplit("/", 1)[0]
    # "March 4, Monday", "Plenary (June 14)", "Jun11 - Wednesday".
    # A folder naming several days ("June 14, 15, 16") gives no single date.
    m = re.search(r"\b([A-Z][a-z]{2})[a-z]*\.? ?(\d{1,2})\b(?!, ?\d)", folder)
    if m and m.group(1).lower() in MONTHS:
        return f"{year}-{MONTHS[m.group(1).lower()]:02d}-{int(m.group(2)):02d}", "folder"
    return event_start, "event"


def clean_title(name):
    """Make a readable draft title from a file name."""
    t = name.strip()
    while re.search(r"\.(pptx?|pdf|key|odp|html)$", t, flags=re.I):  # "x.pptx.pdf"
        t = re.sub(r"\.(pptx?|pdf|key|odp|html)$", "", t, flags=re.I).strip()
    t = re.sub(r"^\d{4} - ", "", t)  # "1130 - " session times (2025)
    t = re.sub(r"^\d\d-\d\d-", "", t)  # "10-50-" session times (2024)
    t = re.sub(r"^\d{1,2}[_ ]", "", t)  # "01_" running order
    t = re.sub(r"^20\d\d-\d\d-\d\d[- _]", "", t)  # "2019-06-19-" (2019, 2020)
    t = re.sub(r"^\d{8}-", "", t)  # "06152017-" (2017)
    t = t.replace("_", " ")
    t = re.sub(r"\s+", " ", t).strip(" -")
    return t


def load_curation(path="curation.json"):
    """Return hand-checked fixes keyed by (source, file_path)."""
    p = Path(path)
    if not p.exists():
        return {}
    return {(c["source"], c["file_path"]): c for c in json.loads(p.read_text())}


def talks():
    curation = load_curation()
    for osf_id, (event, start) in PROJECTS.items():
        for r in json.loads(Path("raw", f"{osf_id}.json").read_text()):
            ext = r["file_name"].rsplit(".", 1)[-1].lower()
            if ext not in SLIDE_EXTENSIONS or (osf_id, r["file_path"]) in SKIP_FILES:
                continue
            date, how = file_date(r["file_path"], start)
            poster = "poster" in r["file_path"].lower()
            talk = {
                "date": date,
                "title": clean_title(r["file_name"]),
                "speakers": [],
                "slides": r["url"],
                "source": f"osf:{osf_id}",
                "type": "poster" if poster else "talk",
                "event": event,
                "date_from": how,
                "file_path": r["file_path"],
            }
            fix = curation.get((talk["source"], talk["file_path"]))
            if fix:
                if fix.get("skip"):
                    continue
                for key in ("title", "speakers", "event", "type"):
                    if fix.get(key):
                        talk[key] = fix[key]
                if fix.get("date"):
                    talk["date"], talk["date_from"] = fix["date"], "checked"
                talk["confidence"] = fix.get("confidence", "")
                talk["evidence"] = fix.get("evidence", "")
            yield talk


def main():
    out = sorted(talks(), key=lambda t: (t["date"], t["source"], t["file_path"]))
    json.dump(out, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
