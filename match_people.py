#!/usr/bin/env python3
"""Match talk speakers to people on people.dataverse.org.

Reads talks.json and the data of a people.dataverse.org checkout, and writes
people.json: {"Speaker Name": "github-username", ...}. Only usernames that
have a page on people.dataverse.org are used.

Usage:
    python3 match_people.py ~/github/gdcc/people.dataverse.org

A name is matched when it equals (ignoring case, accents and punctuation):
- the name on the person's GitHub profile, or
- the speaker of a single-speaker DataverseTV talk listing that username, or
- one of the speakers of a multi-speaker DataverseTV talk, when that speaker's
  name also matches the username's GitHub profile name.

Hand-checked matches go in MANUAL and always win. Speakers who share a
surname with an unmatched member are printed so they can be checked.
"""

import csv
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

# Hand-checked matches that the rules above can't find, e.g. because the
# GitHub profile has no name. Set a name to None to block a wrong match.
MANUAL = {
    "Amber Leahey": "amberleahey",
    "Bethany Seeger": "bseeger",
    "César Ferreira": "cesarpferreira",
    "Dieuwertje Bloemen": "DieuwertjeBloemen",
    "Esther Dzalé Yeumo": "edzale",
    "Germán Saracca": "g-saracca",
    "Ines Schmahl": "ischmahl",
    "Juan Corrales": "juancorr",
    "Juan Pablo Tosca": "jp-tosca",
    "Leonid Andreev": "landreev",
    "Marion Wittenberg": "WittenbergM",
    "Michael Bar-Sinai": "michbarsinai",
    "Paula Saavedra": "PaulaSaav",
    "Thomas Jouneau": "tjouneau",
    "Thu-Mai Christian": "tlchristian",
    "Vaida Plankytė": "vaidap",
    "Vaidas Morkevičius": "vaidasmo",
    "Zacarias Benta": "zbenta",
    # Two members have this GitHub name (josekarvalho, j-n-c); not linked.
    "José Carvalho": None,
}


def norm(name):
    """Lowercase ASCII letters only, so "Mercè Crosas" == "merce crosas"."""
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", name.lower())


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    people_repo = Path(sys.argv[1]).expanduser()
    data = people_repo / "data"

    with open(data / "community-members.tsv", newline="") as f:
        members = {r["GitHub Username"].strip() for r in csv.DictReader(f, delimiter="\t")}
    members.discard("")
    by_lower = {m.lower(): m for m in members}

    profiles = json.loads((data / "github-users.json").read_text())
    profile_name = {}
    for login, entry in profiles.items():
        name = ((entry or {}).get("profile") or {}).get("name") or ""
        if name.strip() and login.lower() in by_lower:
            profile_name[by_lower[login.lower()]] = name.strip()

    # Our own spelling choices apply to DataverseTV names too.
    sys.path.insert(0, str(Path(__file__).parent))
    from talks_from_raw import SPEAKER_ALIASES

    candidates = {}  # norm(name) -> {username: reason}

    def add(name, user, reason):
        name = SPEAKER_ALIASES.get(name, name)
        candidates.setdefault(norm(name), {}).setdefault(user, reason)

    for user, name in profile_name.items():
        add(name, user, "GitHub profile name")

    with open(data / "dataversetv.tsv", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            users = [u.strip() for u in row["GitHub username"].split(",") if u.strip()]
            names = [s.strip() for s in row["Speakers"].split(",") if s.strip()]
            for u in users:
                user = by_lower.get(u.lower())
                if not user:
                    continue
                if len(names) == 1:
                    add(names[0], user, "DataverseTV")
                elif user in profile_name:
                    for n in names:
                        if norm(SPEAKER_ALIASES.get(n, n)) == norm(profile_name[user]):
                            add(n, user, "DataverseTV")

    talks = json.loads(Path("talks.json").read_text())
    counts = Counter(s for t in talks for s in t["speakers"])

    matched, conflicts = {}, []
    for name in counts:
        if name in MANUAL:
            if MANUAL[name]:
                matched[name] = MANUAL[name]
            continue
        found = candidates.get(norm(name), {})
        if len(found) == 1:
            matched[name] = next(iter(found))
        elif len(found) > 1:
            conflicts.append((name, found))

    Path("people.json").write_text(
        json.dumps(dict(sorted(matched.items())), indent=2, ensure_ascii=False) + "\n")

    used = set(matched.values())
    print(f"{len(matched)} of {len(counts)} speakers matched; "
          f"they gave {sum(counts[n] for n in matched)} of {sum(counts.values())} speaker credits")
    for name, found in conflicts:
        print(f"CONFLICT {name}: {found}")

    # Unmatched speakers who share a surname with an unmatched member's profile name.
    surname = lambda n: norm(n.split()[-1]) if n.split() else ""
    free = {}
    for user, name in profile_name.items():
        if user not in used:
            free.setdefault(surname(name), []).append(f"{user} ({name})")
    print("\nPossible matches to check (speaker, talks, members with the same surname):")
    for name, n in counts.most_common():
        if name not in matched and name not in MANUAL and surname(name) in free:
            print(f"  {name} [{n}]: {', '.join(free[surname(name)])}")
    print("\nUnmatched speakers with 3 or more talks:")
    for name, n in counts.most_common():
        if name not in matched and n >= 3:
            print(f"  {name} [{n}]")


if __name__ == "__main__":
    main()
