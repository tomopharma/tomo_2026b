# GCS sync for `md/data/`

Large MD outputs (`*.xtc`, trajectories, MMPBSA results) stay out of git. Use these tools to copy `md/data/` between your laptop and a shared GCS prefix, then pull the same files into an Ephemeral VM session.

**Default GCS prefix:**

```text
gs://ephemeralvm02-ephemeral-work/tomo-2026b/md/data/
```

This lives at the bucket root (not under `users/<id>/home/`), so it is shared across sessions and does not mix with personal gcsfuse home files.

Override with environment variable `TOMO_DATA_GCS_URI` or flag `--uri`.

**Local path:** `md/data/` relative to this repo (`publications/tomo_2026b/md/data/`).

---

## One-time setup (laptop or VM host)

1. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud` and `gsutil`).
2. Authenticate and set the project:

```bash
gcloud auth login
gcloud config set project ephemeralvm02
```

3. Confirm you can read the bucket (optional):

```bash
gsutil ls gs://ephemeralvm02-ephemeral-work/tomo-2026b/md/data/
```

No secrets belong in this repo. Auth uses your local `gcloud` credentials only.

---

## Laptop terminal

From the repo, run the shell wrappers (they call `gcs_data.py`):

```bash
# Upload local md/data/ before an Ephemeral session
./md/tools/upload_data.sh

# Download after a session (or to restore on a new machine)
./md/tools/download_data.sh
```

Optional flags:

```bash
./md/tools/upload_data.sh --uri gs://other-bucket/other/prefix/
./md/tools/download_data.sh --data-dir /path/to/data --quiet
```

Direct Python CLI:

```bash
python3 md/tools/gcs_data.py upload
python3 md/tools/gcs_data.py download
```

---

## Ephemeral VM — before running notebooks

After the repo is cloned (for example under `/workspace/repos/tomo_2026b/`), download data on the **VM host** (gsutil is installed there):

```bash
cd /workspace/repos/tomo_2026b
./md/tools/download_data.sh
```

Or set an explicit data path if your clone lives elsewhere:

```bash
./md/tools/download_data.sh --data-dir /workspace/repos/tomo_2026b/md/data
```

Upload new outputs before the session ends:

```bash
./md/tools/upload_data.sh
```

---

## Jupyter (inside the Ephemeral container)

The GROMACS Jupyter image does not include `gsutil` or `google-cloud-storage` by default. Install the library once per session, then import:

```python
%pip install -q google-cloud-storage

import sys
from pathlib import Path

# Adjust if your clone path differs
md = Path("/workspace/repos/tomo_2026b/md")
sys.path.insert(0, str(md))

from tools.gcs_data import download_data, upload_data

download_data()   # GCS → md/data/
# ... run notebooks ...
upload_data()     # md/data/ → GCS
```

Or open [`sync_data.ipynb`](sync_data.ipynb) in Jupyter and run the cells.

**Alternative:** run `./md/tools/download_data.sh` or `upload_data.sh` in an SSH shell on the VM host (outside the container). That uses `gsutil` and needs no extra Python packages.

---

## Behavior

| Feature | Detail |
| --- | --- |
| Backend | `google-cloud-storage` if installed; otherwise `gsutil -m rsync -r -c` |
| Skip unchanged | CRC / MD5 / size comparison (rsync-like) |
| Excludes | `.DS_Store`, `__pycache__`, `*.tmp`, `.ipynb_checkpoints`, `.Trash-0` |
| Large files | Parallel transfer (`gsutil -m`); per-file log lines in Python mode |

---

## Environment variables

| Variable | Purpose |
| --- | --- |
| `TOMO_DATA_GCS_URI` | Override default `gs://…/tomo-2026b/md/data/` |

Example:

```bash
export TOMO_DATA_GCS_URI=gs://ephemeralvm02-ephemeral-work/tomo-2026b/md/data/
./md/tools/upload_data.sh
```
