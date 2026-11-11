# talks.dataverse.org

An inventory of talks about [Dataverse](https://dataverse.org), recorded or not.

For each talk we want the date, the title, the speaker names, and a link to the slides, stored in a machine-readable format. Recorded talks are already collected by [DataverseTV](https://github.com/IQSS/dataverse-tv), and people in the community are listed at [people.dataverse.org](https://people.dataverse.org).

## Status

Early days. We are starting with talks whose slides were uploaded to [OSF](https://osf.io/awbjp/overview). OSF is freezing soon: existing talks stay there, but new talks can't be added, so slides for new talks will go somewhere else (probably a [Zenodo](https://zenodo.org) community).

## Getting talks from OSF

`osf_inventory.py` goes through an OSF project and all of its components and folders, and prints one JSON record for each file it finds. It uses only the Python standard library, so there's nothing to install.

```
python3 osf_inventory.py awbjp > raw.json
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

`raw.json` is a raw dump of the files. The next step is to turn it into a list of talks with these fields:

```json
{
  "date": "YYYY-MM-DD",
  "title": "…",
  "speakers": ["…"],
  "slides": "https://osf.io/…/",
  "source": "osf:awbjp"
}
```

Upload dates on OSF are a stand-in for when a talk was given, so they should be checked against event dates.

## Contributing

Know of a talk that's missing? Open an issue or a pull request.
