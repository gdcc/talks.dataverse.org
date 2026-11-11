# talks.dataverse.org

An inventory of talks about [Dataverse](https://dataverse.org), recorded or not.

For each talk we want the date, the title, the speaker names, and a link to the slides, stored in a machine-readable format. Recorded talks are already collected by [DataverseTV](https://github.com/IQSS/dataverse-tv), and people in the community are listed at [people.dataverse.org](https://people.dataverse.org).

## Status

Early days. We are starting with talks whose slides were uploaded to [OSF](https://osf.io). `talks.json` has 351 records (talks and posters) from these OSF projects:

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

There's no OSF project for the 2018 community meeting. OSF is freezing soon: existing talks stay there, but new talks can't be added, so slides for new talks will go somewhere else (probably a [Zenodo](https://zenodo.org) community).

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

It also adds `type` (`talk` or `poster`), `event`, `file_path` (where the file sits on OSF), and `date_from`, which says where the date came from:

- `file`: a date in the file name
- `folder`: a day in the OSF folder name
- `event`: no day was found, so it's the event's first day and still needs checking against the agenda

Upload dates aren't used, because some years were uploaded months after the meeting.

Still to do:

- `speakers` is empty everywhere. OSF only records who uploaded the files, so speakers need to come from file names or meeting agendas.
- Titles are cleaned-up file names. Many still have the speaker's name in them, or aren't the real talk title.

## Contributing

Know of a talk that's missing? Open an issue or a pull request.
