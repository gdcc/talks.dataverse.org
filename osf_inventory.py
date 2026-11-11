#!/usr/bin/env python3
"""Inventory talks stored in an OSF project.

Walks an OSF project (and its components) through the OSF API v2 and
prints one JSON record per file. Uses only the Python standard library.

Usage:
    python3 osf_inventory.py awbjp > raw.json
"""

import json
import sys
import time
import urllib.error
import urllib.request

API = "https://api.osf.io/v2"


def get(url):
    """GET a URL from the OSF API and return the parsed JSON."""
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                time.sleep(2 ** attempt)
                continue
            raise


def get_all(url):
    """Yield every item from a paginated OSF API listing."""
    while url:
        page = get(url)
        yield from page["data"]
        url = page["links"].get("next")


def contributors(node_id):
    """Return the names of a node's bibliographic contributors, in order."""
    url = f"{API}/nodes/{node_id}/contributors/?embed=users&page[size]=100"
    names = []
    for c in get_all(url):
        if not c["attributes"].get("bibliographic", True):
            continue
        user = c.get("embeds", {}).get("users", {}).get("data")
        if user:
            names.append(user["attributes"]["full_name"])
        elif c["attributes"].get("unregistered_contributor"):
            names.append(c["attributes"]["unregistered_contributor"])
    return names


def files(node_id):
    """Yield every file in a node's OSF Storage, descending into folders."""
    stack = [f"{API}/nodes/{node_id}/files/osfstorage/?page[size]=100"]
    while stack:
        for item in get_all(stack.pop()):
            if item["attributes"]["kind"] == "folder":
                stack.append(
                    item["relationships"]["files"]["links"]["related"]["href"]
                    + "?page[size]=100"
                )
            else:
                yield item


def walk(node_id, parents=()):
    """Yield one record per file in this node and all its components."""
    node = get(f"{API}/nodes/{node_id}/")["data"]
    attrs = node["attributes"]
    path = parents + (attrs["title"],)
    people = contributors(node_id)
    for f in files(node_id):
        fa = f["attributes"]
        guid = fa.get("guid")
        yield {
            "node_id": node_id,
            "node_path": list(path),
            "node_description": attrs.get("description") or "",
            "node_date_created": attrs.get("date_created"),
            "contributors": people,
            "file_name": fa["name"],
            "file_path": fa.get("materialized_path"),
            "file_date_created": fa.get("date_created"),
            "file_size": fa.get("size"),
            "url": f"https://osf.io/{guid}/" if guid else f["links"].get("html"),
            "download": f["links"].get("download"),
        }
    for child in get_all(f"{API}/nodes/{node_id}/children/?page[size]=100"):
        yield from walk(child["id"], path)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    records = list(walk(sys.argv[1]))
    json.dump(records, sys.stdout, indent=2, ensure_ascii=False)
    print()


if __name__ == "__main__":
    main()
