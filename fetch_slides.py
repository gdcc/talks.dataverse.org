#!/usr/bin/env python3
"""Download slides into cache/ for make_thumbnails.py.

For every talk in talks.json from OSF or DataverseTV, looks for its slides in
cache/ (named by cache_name() in talks_from_raw.py) and downloads the ones
that are missing. cache/ is gitignored.

Usage:
    python3 fetch_slides.py
    python3 make_thumbnails.py
    python3 talks_from_raw.py > talks.json

OSF slides are downloaded with the link osf_inventory.py recorded in
raw/<project>.json and kept only if their size matches that record.

DataverseTV slides are on many sites. A talk's file is looked for, in order:
- DataverseTV's own download link, if it has one
- a direct download for Google Slides, Docs and Drive, Dropbox, Seafile,
  Nextcloud and OSF links, or the link itself if it ends in .pdf or .pptx
- on a landing page (Zenodo, DSpace, dataverse.org and so on), the one
  PDF or PowerPoint file it links to, if it links to exactly one
A download is kept only if it really is a PDF or PowerPoint file. Talks whose
slides can't be found this way (Google Groups, SlideShare, Canva...) are
listed at the end.
"""

import io
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from talks_from_raw import cache_name

CACHE = Path("cache")
SLIDE_EXTENSIONS = {"pdf", "pptx", "ppt", "key", "odp"}
MAX_BYTES = 300 * 1024 * 1024
WEB_SOURCES = {"dataversetv"}


def get(url, max_bytes=MAX_BYTES):
    """GET a URL and return (bytes, content type, final URL). Retries a few times."""
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url), timeout=120) as resp:
                data = resp.read(max_bytes + 1)
                if len(data) > max_bytes:
                    raise ValueError("file too large")
                return data, resp.headers.get("Content-Type", ""), resp.geturl()
        except urllib.error.HTTPError as e:
            if e.code in (401, 403, 404, 410):
                raise
            err = e
        except (OSError, ValueError) as e:
            err = e
        time.sleep(5 * (attempt + 1))
    raise err


def slide_type(data):
    """'pdf' or 'pptx' if data is a slide file, else None."""
    if data[:5] == b"%PDF-":
        return "pdf"
    if data[:4] == b"PK\x03\x04":
        try:
            names = zipfile.ZipFile(io.BytesIO(data)).namelist()
        except zipfile.BadZipFile:
            return None
        if any(n.startswith("ppt/") for n in names):
            return "pptx"
    return None


def direct_links(url):
    """Links that should give the file itself, worked out from the slides link."""
    u = urllib.parse.urlsplit(url)
    host, path = u.netloc.lower().removeprefix("www."), u.path
    m = re.match(r"/presentation/d/([\w-]+)", path)
    if host == "docs.google.com" and m:
        return [f"https://docs.google.com/presentation/d/{m.group(1)}/export/pdf"]
    m = re.match(r"/document/d/([\w-]+)", path)
    if host == "docs.google.com" and m:
        return [f"https://docs.google.com/document/d/{m.group(1)}/export?format=pdf"]
    m = re.match(r"/file/d/([\w-]+)", path)
    if host == "drive.google.com" and m:
        return [f"https://drive.google.com/uc?export=download&id={m.group(1)}"]
    if host == "dropbox.com":
        q = urllib.parse.parse_qs(u.query)
        q["dl"] = ["1"]
        return [urllib.parse.urlunsplit(u._replace(query=urllib.parse.urlencode(q, doseq=True)))]
    m = re.match(r"/f/(\w+)/?$", path)
    if m:  # Seafile share link, e.g. heibox.uni-heidelberg.de
        return [f"{u.scheme}://{u.netloc}/f/{m.group(1)}/?dl=1"]
    m = re.match(r"/s/(\w+)/?$", path)
    if m:  # Nextcloud share link
        return [f"{u.scheme}://{u.netloc}/s/{m.group(1)}/download"]
    m = re.match(r"/([a-z0-9]{5})/?$", path)
    if host == "osf.io" and m:
        return [f"https://osf.io/download/{m.group(1)}/"]
    if path.lower().rsplit(".", 1)[-1] in SLIDE_EXTENSIONS:
        return [url]
    return []


def linked_file(page, base):
    """The one slide file a landing page links to, or None if there isn't exactly one."""
    html = page.decode("utf-8", "replace")
    found = set()
    for href in re.findall(r'href=["\']([^"\'#]+)', html):
        link = urllib.parse.urljoin(base, href.replace("&amp;", "&"))
        if urllib.parse.urlsplit(link).path.lower().rsplit(".", 1)[-1] in SLIDE_EXTENSIONS:
            found.add(link)
    return found.pop() if len(found) == 1 else None


def fetch_web(talk):
    """Find and download a talk's slides. Returns (bytes, type) or raises."""
    tried = []
    for url in filter(None, [talk.get("slides_download"), *direct_links(talk["slides"])]):
        tried.append(url)
        data, _, _ = get(url)
        if kind := slide_type(data):
            return data, kind
    m = re.search(r"10\.5281/zenodo\.(\d+)", talk["slides"])
    if m:  # Zenodo lists a record's files in its API, not in the page HTML.
        record = json.loads(get(f"https://zenodo.org/api/records/{m.group(1)}")[0])
        files = [f for f in record.get("files", [])
                 if f["key"].lower().rsplit(".", 1)[-1] in SLIDE_EXTENSIONS]
        if len(files) == 1:
            data, _, _ = get(files[0]["links"]["self"])
            if kind := slide_type(data):
                return data, kind
    data, ctype, final = get(talk["slides"], max_bytes=MAX_BYTES)
    if kind := slide_type(data):
        return data, kind
    if "html" in ctype:
        link = linked_file(data, final)
        if link and link not in tried:
            data, _, _ = get(link)
            if kind := slide_type(data):
                return data, kind
    raise ValueError("no PDF or PowerPoint file found")


def fetch_osf(record, dest):
    data, _, _ = get(record["download"])
    if len(data) != record["file_size"]:
        raise ValueError(f"got {len(data)} bytes, expected {record['file_size']}")
    dest.write_bytes(data)


def main():
    records = {r["url"]: r for f in Path("raw").glob("*.json") for r in json.loads(f.read_text())}
    talks = json.loads(Path("talks.json").read_text())

    have, fetched, failed, skipped = 0, 0, [], 0
    for t in talks:
        name = cache_name(t.get("slides"))
        osf = t["source"].startswith("osf:")
        if not name or not (osf or t["source"] in WEB_SOURCES):
            continue
        if list(CACHE.glob(name + ".*")):
            have += 1
            continue
        (CACHE / name).parent.mkdir(parents=True, exist_ok=True)
        try:
            if osf:
                r = records.get(t["slides"])
                ext = r["file_name"].rsplit(".", 1)[-1].lower() if r else ""
                if not r or not r.get("download") or ext not in SLIDE_EXTENSIONS:
                    skipped += 1
                    continue
                print(f"fetching {name}.{ext}: {t['title'][:60]}")
                fetch_osf(r, CACHE / f"{name}.{ext}")
            else:
                print(f"fetching {name}: {t['title'][:60]}")
                data, ext = fetch_web(t)
                (CACHE / f"{name}.{ext}").write_bytes(data)
            fetched += 1
        except Exception as e:
            failed.append(f"{t['date']} {t['title'][:60]} | {t['slides'][:80]} | {e}")

    print(f"\n{fetched} fetched, {have} already cached, {skipped} skipped (not a slide file), "
          f"{len(failed)} not found:")
    for f in failed:
        print("  " + f)


if __name__ == "__main__":
    main()
