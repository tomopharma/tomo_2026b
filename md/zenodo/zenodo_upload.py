#!/usr/bin/env python3
"""Upload the staged deposit (build_deposit.sh) to a Zenodo *draft*. Never publishes.

Usage:
    python zenodo_upload.py --dry-run                 # show what would happen
    python zenodo_upload.py --sandbox                 # rehearse on sandbox.zenodo.org
    python zenodo_upload.py                           # create (or resume) the real draft

The token is read from $ZENODO_TOKEN or ~/.config/zenodo/token (one line; chmod 600). It needs the
scopes deposit:write and deposit:actions. A sandbox token comes from sandbox.zenodo.org and only
works there.

The first run creates a draft with a reserved DOI and records its id in <stage>/zenodo_state.json;
later runs resume that draft and skip files already uploaded with the same MD5. Publishing is a
manual step on the Zenodo web page, because a published record cannot be deleted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import requests

HERE = Path(__file__).resolve().parent
HOSTS = {False: "https://zenodo.org", True: "https://sandbox.zenodo.org"}


def read_token() -> str:
    token = os.environ.get("ZENODO_TOKEN", "").strip()
    path = Path.home() / ".config" / "zenodo" / "token"
    if not token and path.is_file():
        token = path.read_text().strip()
    if not token:
        sys.exit(f"No token: set ZENODO_TOKEN or write it to {path}")
    return token


def md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 24), b""):
            h.update(chunk)
    return h.hexdigest()


class Zenodo:
    def __init__(self, host: str, token: str):
        self.api = f"{host}/api"
        self.session = requests.Session()
        self.session.headers["Authorization"] = f"Bearer {token}"

    def call(self, method: str, url: str, **kwargs) -> dict:
        response = self.session.request(method, url, timeout=kwargs.pop("timeout", 120), **kwargs)
        if not response.ok:
            sys.exit(f"{method} {url} failed ({response.status_code}): {response.text[:2000]}")
        return response.json() if response.content else {}

    def create_draft(self) -> dict:
        return self.call("POST", f"{self.api}/deposit/depositions", json={"metadata": {"prereserve_doi": True}})

    def get_draft(self, dep_id: int) -> dict:
        return self.call("GET", f"{self.api}/deposit/depositions/{dep_id}")

    def bucket_files(self, bucket: str) -> dict[str, str]:
        """{filename: md5} already in the draft's bucket."""
        contents = self.call("GET", bucket).get("contents", [])
        return {c["key"]: c.get("checksum", "").removeprefix("md5:") for c in contents}

    def upload(self, bucket: str, path: Path) -> dict:
        with path.open("rb") as fh:  # requests streams a file object; the file is never read into memory
            return self.call("PUT", f"{bucket}/{path.name}", data=fh, timeout=None)

    def set_metadata(self, dep_id: int, metadata: dict) -> dict:
        return self.call("PUT", f"{self.api}/deposit/depositions/{dep_id}", json={"metadata": metadata})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--stage", type=Path, default=Path(os.environ.get("STAGE", Path.home() / "zenodo_tomo_2026b")))
    parser.add_argument("--metadata", type=Path, default=HERE / "metadata.json")
    parser.add_argument("--sandbox", action="store_true", help="use sandbox.zenodo.org (test records)")
    parser.add_argument("--dry-run", action="store_true", help="check inputs and print the plan; no network calls")
    args = parser.parse_args()

    upload_dir = args.stage / "upload"
    files = sorted(p for p in upload_dir.iterdir() if p.is_file()) if upload_dir.is_dir() else []
    if not files or not (upload_dir / "MANIFEST.sha256").is_file():
        sys.exit(f"No staged deposit in {upload_dir}: run build_deposit.sh first")
    if len(files) > 100:
        sys.exit(f"{len(files)} files; Zenodo allows 100 per record")
    metadata = json.loads(args.metadata.read_text())
    if "TODO" in json.dumps(metadata):
        sys.exit(f"{args.metadata} still contains TODO placeholders (creators, affiliations)")

    host = os.environ.get("ZENODO_HOST") or HOSTS[args.sandbox]  # ZENODO_HOST: tests against a local mock
    state_path = args.stage / ("zenodo_state_sandbox.json" if args.sandbox else "zenodo_state.json")
    state = json.loads(state_path.read_text()) if state_path.is_file() else {}
    total_gb = sum(p.stat().st_size for p in files) / 1e9
    print(f"{host}: {len(files)} files, {total_gb:.1f} GB from {upload_dir}")
    print(f"Draft: {'resume ' + str(state['id']) if state.get('id') else 'create new (DOI reserved)'}")
    if args.dry_run:
        for p in files:
            print(f"  {p.stat().st_size / 1e6:10.1f} MB  {p.name}")
        return

    zenodo = Zenodo(host, read_token())
    draft = zenodo.get_draft(state["id"]) if state.get("id") else zenodo.create_draft()
    if draft.get("submitted"):
        sys.exit(f"Deposition {draft['id']} is already published; start a new version on the web page instead")
    reserved = draft["metadata"].get("prereserve_doi")  # {"doi": …} once reserved; may echo back as True
    doi = reserved.get("doi") if isinstance(reserved, dict) else state.get("doi")
    state.update(id=draft["id"], doi=doi, url=draft["links"]["html"])
    state_path.write_text(json.dumps(state, indent=1) + "\n")

    bucket = draft["links"]["bucket"]
    present = zenodo.bucket_files(bucket)
    for p in files:
        if p.name in present and present[p.name] == md5(p):
            print(f"  skip   {p.name} (already uploaded)")
            continue
        print(f"  upload {p.name} ({p.stat().st_size / 1e9:.2f} GB) …", flush=True)
        result = zenodo.upload(bucket, p)
        if result.get("checksum", "").removeprefix("md5:") != md5(p):
            sys.exit(f"Checksum mismatch after uploading {p.name}; rerun to retry")

    zenodo.set_metadata(draft["id"], {**metadata, "prereserve_doi": True})  # keep the reserved DOI
    print(f"\nDraft ready, NOT published.\n  DOI (reserved): {doi}\n  Review and publish: {state['url']}")


if __name__ == "__main__":
    main()
