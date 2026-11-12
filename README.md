# talks.dataverse.org

An inventory of talks about [Dataverse](https://dataverse.org), recorded or not.

For each talk we want the date, the title, the speaker names, and a link to the slides, stored in a machine-readable format. Recorded talks are already collected by [DataverseTV](https://github.com/IQSS/dataverse-tv), and people in the community are listed at [people.dataverse.org](https://people.dataverse.org).

## Status

Early days. We are starting with talks whose slides were uploaded to [OSF](https://osf.io). `talks.json` has 547 records: 499 talks, 22 tutorials, 15 posters, 6 panels and 5 workshops, from 2014 to 2026. They come from OSF, meeting agendas and DataverseTV. Most come from these OSF projects:

| OSF ID | Event |
|---|---|
| [3xcq8](https://osf.io/3xcq8/), [e5n3h](https://osf.io/e5n3h/) | Dataverse Community Meeting 2017 |
| [ke9gc](https://osf.io/ke9gc/) | Open Repositories 2018 (Dataverse panel) |
| [h8yjw](https://osf.io/h8yjw/) | Dataverse Community Meeting 2019 |
| [prq46](https://osf.io/prq46/) | Dataverse Community Meeting 2020 |
| [gav6m](https://osf.io/gav6m/) | Dataverse Community Meeting 2021 |
| [fqmwb](https://osf.io/fqmwb/) | Dataverse Community Meeting 2022 |
| [5k47u](https://osf.io/5k47u/) | Dataverse Community Meeting 2023 |
| [95ycg](https://osf.io/95ycg/) | Dataverse Community Meeting 2024 |
| [j4r2e](https://osf.io/j4r2e/) | Dataverse Community Meeting 2025 |
| [awbjp](https://osf.io/awbjp/) | Dataverse Community Meeting 2026 |
| [wpixk](https://osf.io/wpixk/) | Mercè Crosas, 2014 (one talk) |

There's no OSF project for the 2015, 2016 or 2018 community meetings. Talks for those come from the meeting agendas and are kept by hand in `extra_talks.json` (see below):

- 2015: the [agenda](https://dataversecommunitymeeting.hsites.harvard.edu/agenda) and [pre-meeting workshop](https://dataversecommunitymeeting.hsites.harvard.edu/premeeting-workshop). Slides are on SlideShare where they exist.
- 2016: the [agenda](https://dcm2016.hsites.harvard.edu/meeting-agenda) and [privacy workshop](https://dcm2016.hsites.harvard.edu/privacy-workshop). Slides are on the meeting site; titles come from the title slides, since the agenda only lists speakers.
- 2018: the [Sched agenda](https://dataversecommunitymeeting20.sched.com/list/descriptions/), which also hosts the slides.

Talks that were recorded for [DataverseTV](https://github.com/IQSS/dataverse-tv) and have slides are included too: community calls, webinars, tutorials and talks at other events. They're in `dataversetv_talks.json` (see below).

OSF is freezing soon: existing talks stay there, but new talks can't be added, so slides for new talks will go somewhere else (probably a [Zenodo](https://zenodo.org) community).

## Getting talks from OSF

`osf_inventory.py` goes through an OSF project and all of its components and folders, and prints one JSON record for each file it finds. It uses only the Python standard library, so there's nothing to install.

```
python3 osf_inventory.py awbjp > raw/awbjp.json
```

The argument is the OSF project ID, the part of the URL after `osf.io/`.

Each record looks like this:

| Field | Meaning |
|---|---|
| `node_id` | OSF ID of the project or component that holds the file |
| `node_path` | Titles from the top-level project down to that component |
| `node_description` | Description of that component |
| `node_date_created` | When the component was created on OSF |
| `contributors` | Names of the component's bibliographic contributors |
| `file_name` | File name, e.g. `slides.pdf` |
| `file_path` | Path of the file inside OSF Storage |
| `file_date_created` | When the file was uploaded |
| `file_size` | Size in bytes |
| `url` | Link to view the file on OSF |
| `download` | Direct download link |

The script reads only public data and doesn't need an OSF account. If OSF rate-limits it, it waits and retries.

## From raw records to talks

Each `raw/<id>.json` is a raw dump of the files in one project. `talks_from_raw.py` turns them into `talks.json`:

```
python3 talks_from_raw.py > talks.json
```

It keeps slides (PDF, PowerPoint, HTML) and skips recordings, photos and other files. Each talk has these fields:

```json
{
  "date": "YYYY-MM-DD",
  "title": "…",
  "speakers": ["…"],
  "slides": "https://osf.io/…/",
  "source": "osf:awbjp"
}
```

It also adds `type` (`talk`, `tutorial`, `poster`, `panel` or `workshop`), `event`, `file_path` (where the file sits on OSF), and `date_from`, which says where the date came from:

- `checked`: from `curation.json` (see below)
- `file`: a date in the file name
- `folder`: a day in the OSF folder name
- `event`: no day was found, so it's the event's first day

Upload dates aren't used, because some years were uploaded months after the meeting.

## Curation

OSF doesn't say who gave a talk, so speakers, real titles and dates were checked by hand against meeting agendas (live or on the Wayback Machine), DataverseTV, and the title slides of the PDFs. The results are in `curation.json`, keyed by `source` and `file_path`, and `talks_from_raw.py` applies them over what it works out from OSF. Each entry has a `confidence` (`high`, `medium` or `low`), the `evidence` used, and `notes` for anything odd.

To add or fix entries, edit `curation.json` directly, or merge a JSON array of entries in the same shape:

```
python3 merge_curation.py new-entries.json
python3 talks_from_raw.py > talks.json
```

Talks that aren't on OSF go in `extra_talks.json`, already in the final talk format, with `slides` set to a link (e.g. SlideShare) or `null` when there are no slides. `talks_from_raw.py` adds them to `talks.json`.

Some people's names are spelled differently from year to year. `SPEAKER_ALIASES` in `talks_from_raw.py` maps each variant to one spelling, so a search finds all of a person's talks.

### DataverseTV

`dataversetv_talks.py` reads the DataverseTV spreadsheet, as cached in a [people.dataverse.org](https://github.com/gdcc/people.dataverse.org) checkout, and writes `dataversetv_talks.json`. It contains every DataverseTV talk with a slides link that isn't already listed:

```
python3 dataversetv_talks.py ~/github/gdcc/people.dataverse.org/data/dataversetv.tsv
python3 talks_from_raw.py > talks.json
```

A DataverseTV talk counts as already listed when its slides are the same OSF file, or when a listed talk is within 4 days and shares a speaker or has a very similar title. Recordings of whole 2020 and 2021 meeting sessions are skipped, since their "slides" link is just the agenda page. These talks have a `video` link, and their `event` is empty because DataverseTV doesn't record it.

Files that aren't talks (a panel proposal, a speaker bio, duplicate uploads) are listed in `SKIP_FILES` in `talks_from_raw.py`.

Still open:

- Six talks have no speakers: five 2017 developer workshop sessions credited only to "Dataverse Team", and the 2023 demo session's intro slides.
- The 2025 agenda is gone (it was on Cvent), so 2025 speakers and titles come from title slides and are listed in the order printed there.

## Thumbnails

Talks show a small image of their first slide when the slides could be downloaded. Making them takes three steps:

```
python3 fetch_slides.py
python3 make_thumbnails.py
python3 talks_from_raw.py > talks.json
```

1. `fetch_slides.py` downloads the slides of every OSF and DataverseTV talk in `talks.json` into `cache/`, which is gitignored, skipping files already there.
   - **OSF:** it uses the download link that `osf_inventory.py` records for each file and keeps a file only if its size matches OSF's record.
   - **DataverseTV:** slides are on many sites. It tries DataverseTV's own download link, then a direct download worked out from the link (Google Slides, Docs and Drive, Dropbox, Seafile, Nextcloud, OSF, Zenodo, or a link straight to a PDF), then the one PDF or PowerPoint file a landing page links to. A download is kept only if it's really a PDF or PowerPoint file. It lists the talks whose slides it couldn't get.

   Files are named the way `cache_name()` in `talks_from_raw.py` gives: `cache/osf/<osf id>.pdf`, `cache/osf/<project>-<file id>.pdf` for OSF files without a short ID, and `cache/web/<hash>.pdf` for everything else, where the hash is from the slides link.
2. `make_thumbnails.py` writes a 560-pixel-wide WebP image of each file's first page to `thumbs/`, which is committed. That's sharp at the size the site shows them, at about 12 KB each (about 5 MB for 394). It skips images that already exist at that width, so changing `WIDTH` in the script remakes them all.
3. Regenerating `talks.json` adds a `thumb` field to every talk that has a thumbnail.

`make_thumbnails.py` needs `pdftoppm` (from Poppler) and Pillow. PowerPoint files are rendered with macOS Quick Look.

So far 394 talks have thumbnails:

- **OSF:** 344 of 345. The one without has an HTML page for slides.
- **DataverseTV:** 50 of 96. The others couldn't be downloaded:
  - their links are dead (most old dataverse.org presentation pages, one deleted Google Slides deck)
  - the site blocks scripts (scholar.harvard.edu, datascience.nih.gov, Canva, dataverse.lv and a few more)
  - or the link isn't to a file (Google Groups posts, GitHub, SlideShare, YouTube, DSpace pages at TDL)
- **Agenda talks:** the 2015, 2016 and 2018 talks have no thumbnails yet.

## Website

`index.html` has two views of `talks.json`:

- **Talks** (`#/`): every talk, newest first, as a grid of cards per year, with a search box. Each card leads with the first slide, linked to the slides; talks without a thumbnail show their title in its place.
- **Speakers** (`#/speakers`): everyone who has given a talk, with a picture, how many talks and the years they spoke, most talks first. Speakers linked to Dataverse People show their GitHub profile picture, loaded live from GitHub; everyone else, or anyone whose picture doesn't load, gets a circle with their initials in a color worked out from their name. Clicking a name, here or under a talk, shows that person's talks (`#/speaker/<name>`).

Talks without slides aren't shown on the website, and don't count toward anyone's total. They stay in `talks.json` with `"slides": null`, so nothing is lost. To see which ones are hidden:

```
python3 hidden_talks.py
```

It lists them by year and says where to add each one's slides link: `extra_talks.json` for talks from agendas, or the DataverseTV spreadsheet for DataverseTV talks. Once a talk has a slides link and `talks.json` is regenerated, it shows up on the site. A DataverseTV "slides" link that's just the recording counts as no slides.

Panels, posters and workshops count as talks for each person listed on them.

### Linking speakers to Dataverse People

Speakers who are on [people.dataverse.org](https://people.dataverse.org) show their GitHub username, linked to their page there (e.g. [@qqmyers](https://people.dataverse.org/qqmyers)). The links come from `people.json`, which `match_people.py` builds from a checkout of [gdcc/people.dataverse.org](https://github.com/gdcc/people.dataverse.org):

```
python3 match_people.py ~/github/gdcc/people.dataverse.org
```

A speaker is linked when their name matches a member's GitHub profile name, or a DataverseTV talk that lists the member's username. Matches that need a person to check go in `MANUAL` in `match_people.py`. The script prints speakers it couldn't match for sure, so they can be checked. Many frequent speakers aren't on people.dataverse.org yet, so they have no link. It's a static page, so it can be served as is, for example by GitHub Pages. To try it locally:

```
python3 -m http.server 8765
```

and open http://localhost:8765.

## Contributing

Know of a talk that's missing? Open an issue or a pull request.
