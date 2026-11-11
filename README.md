# talks.dataverse.org

An inventory of talks about [Dataverse](https://dataverse.org), recorded or not.

For each talk we want the date, the title, the speaker names, and a link to the slides, stored in a machine-readable format. Recorded talks are already collected by [DataverseTV](https://github.com/IQSS/dataverse-tv), and people in the community are listed at [people.dataverse.org](https://people.dataverse.org).

## Status

Early days. We are starting with talks whose slides were uploaded to [OSF](https://osf.io). `talks.json` has 451 records: 425 talks, 15 posters, 6 panels and 5 workshops, from 2014 to 2026. Most come from these OSF projects:

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

It also adds `type` (`talk`, `poster`, `panel` or `workshop`), `event`, `file_path` (where the file sits on OSF), and `date_from`, which says where the date came from:

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

Files that aren't talks (a panel proposal, a speaker bio, duplicate uploads) are listed in `SKIP_FILES` in `talks_from_raw.py`.

Still open:

- Six talks have no speakers: five 2017 developer workshop sessions credited only to "Dataverse Team", and the 2023 demo session's intro slides.
- The 2025 agenda is gone (it was on Cvent), so 2025 speakers and titles come from title slides and are listed in the order printed there.

## Website

`index.html` has two views of `talks.json`:

- **Talks** (`#/`): every talk, newest first, with a search box.
- **Speakers** (`#/speakers`): everyone who has given a talk, with how many and the years they spoke, most talks first. Clicking a name, here or under a talk, shows that person's talks (`#/speaker/<name>`).

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
