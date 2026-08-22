#!/usr/bin/env python3
"""Upload or download md/data/ to a shared GCS prefix.

Uses google-cloud-storage when installed; otherwise gsutil rsync.
Skips unchanged files (checksum / size) and excludes common junk paths.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Iterator, Optional

DEFAULT_GCS_URI = "gs://ephemeralvm02-ephemeral-work/tomo-2026b/md/data/"
ENV_GCS_URI = "TOMO_DATA_GCS_URI"

# Regex for gsutil rsync -x (exclude paths that match any part).
GSUTIL_EXCLUDE_REGEX = (
    r"(^|/)\.DS_Store$"
    r"|(^|/)__pycache__(/|$)"
    r"|\.tmp$"
    r"|(^|/)\.ipynb_checkpoints(/|$)"
    r"|(^|/)\.Trash-0(/|$)"
)

# Glob-style patterns for the Python backend.
EXCLUDE_GLOBS = (
    ".DS_Store",
    "__pycache__",
    "*.tmp",
    ".ipynb_checkpoints",
    ".Trash-0",
)


def md_root() -> Path:
    """Return the md/ directory (parent of tools/)."""
    return Path(__file__).resolve().parent.parent


def default_data_dir() -> Path:
    return md_root() / "data"


def resolve_gcs_uri(uri: Optional[str] = None) -> str:
    value = (uri or os.environ.get(ENV_GCS_URI) or DEFAULT_GCS_URI).strip()
    if not value.startswith("gs://"):
        raise ValueError(f"GCS URI must start with gs://, got: {value!r}")
    if not value.endswith("/"):
        value += "/"
    return value


def parse_gcs_uri(uri: str) -> tuple[str, str]:
    """Return (bucket_name, object_prefix) with trailing slash on prefix."""
    path = uri[5:]
    bucket, sep, prefix = path.partition("/")
    if not bucket:
        raise ValueError(f"Invalid GCS URI (no bucket): {uri!r}")
    if sep and prefix:
        prefix = prefix.rstrip("/") + "/"
    else:
        prefix = ""
    return bucket, prefix


def should_exclude(rel_posix: str) -> bool:
    parts = rel_posix.split("/")
    for part in parts:
        if part == ".DS_Store" or part == "__pycache__" or part == ".ipynb_checkpoints":
            return True
        if part == ".Trash-0":
            return True
    name = parts[-1] if parts else rel_posix
    return fnmatch.fnmatch(name, "*.tmp")


def iter_local_files(data_dir: Path) -> Iterator[tuple[Path, str]]:
    """Yield (absolute_path, relative_posix_path) for files under data_dir."""
    data_dir = data_dir.resolve()
    if not data_dir.is_dir():
        return
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(data_dir).as_posix()
        if should_exclude(rel):
            continue
        yield path, rel


def local_md5(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _human_size(num_bytes: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    size = float(num_bytes)
    for unit in units:
        if size < 1024.0 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{num_bytes} B"


def _log(message: str, verbose: bool = True) -> None:
    if verbose:
        print(message, flush=True)


def _have_gcs_library() -> bool:
    try:
        import google.cloud.storage  # noqa: F401

        return True
    except ImportError:
        return False


def _have_gsutil() -> bool:
    return shutil.which("gsutil") is not None


def _run_gsutil_rsync(
    *,
    source: str,
    destination: str,
    verbose: bool,
) -> None:
    if not _have_gsutil():
        raise RuntimeError(
            "Neither google-cloud-storage nor gsutil is available.\n"
            "  Laptop: install Google Cloud SDK (gsutil).\n"
            "  Jupyter (Ephemeral container): run once:\n"
            "    %pip install google-cloud-storage\n"
            "  Or run upload_data.sh / download_data.sh on the VM host."
        )

    cmd = [
        "gsutil",
        "-m",
        "rsync",
        "-r",
        "-c",
        "-x",
        GSUTIL_EXCLUDE_REGEX,
    ]
    cmd.extend([source, destination])

    _log(f"Running: {' '.join(cmd)}", verbose=True)
    subprocess.run(cmd, check=True)


def _sync_with_gcs_library(
    *,
    data_dir: Path,
    gcs_uri: str,
    direction: str,
    verbose: bool,
) -> dict[str, int]:
    from google.cloud import storage

    bucket_name, prefix = parse_gcs_uri(gcs_uri)
    client = storage.Client()
    bucket = client.bucket(bucket_name)

    stats = {"skipped": 0, "transferred": 0, "bytes": 0}

    if direction == "upload":
        for abs_path, rel in iter_local_files(data_dir):
            blob_name = prefix + rel
            blob = bucket.blob(blob_name)
            size = abs_path.stat().st_size
            if blob.exists(client):
                blob.reload(client)
                if blob.size == size:
                    local_hash = local_md5(abs_path)
                    remote_hash = (blob.md5_hash or "").strip()
                    if remote_hash:
                        import base64

                        remote_hex = base64.b64decode(remote_hash).hex()
                        if local_hash == remote_hex:
                            stats["skipped"] += 1
                            if verbose:
                                _log(f"skip (unchanged): {rel}")
                            continue
                    elif blob.updated and blob.updated.timestamp() >= abs_path.stat().st_mtime:
                        stats["skipped"] += 1
                        if verbose:
                            _log(f"skip (same size, newer remote): {rel}")
                        continue

            _log(f"upload {_human_size(size)}: {rel}", verbose=True)
            blob.upload_from_filename(str(abs_path), checksum="md5")
            stats["transferred"] += 1
            stats["bytes"] += size

    elif direction == "download":
        data_dir.mkdir(parents=True, exist_ok=True)
        for blob in client.list_blobs(bucket, prefix=prefix):
            if blob.name.endswith("/"):
                continue
            rel = blob.name[len(prefix) :] if blob.name.startswith(prefix) else blob.name
            if not rel or should_exclude(rel):
                continue

            dest = data_dir / rel
            dest.parent.mkdir(parents=True, exist_ok=True)

            if dest.is_file():
                local_size = dest.stat().st_size
                if blob.size == local_size:
                    remote_hash = (blob.md5_hash or "").strip()
                    if remote_hash:
                        import base64

                        remote_hex = base64.b64decode(remote_hash).hex()
                        if local_md5(dest) == remote_hex:
                            stats["skipped"] += 1
                            if verbose:
                                _log(f"skip (unchanged): {rel}")
                            continue

            size = blob.size or 0
            _log(f"download {_human_size(size)}: {rel}", verbose=True)
            blob.download_to_filename(str(dest))
            stats["transferred"] += 1
            stats["bytes"] += size
    else:
        raise ValueError(f"Unknown direction: {direction!r}")

    return stats


def _sync(
    *,
    data_dir: Path,
    gcs_uri: str,
    direction: str,
    verbose: bool,
) -> dict[str, int]:
    data_dir = data_dir.resolve()
    gcs_uri = resolve_gcs_uri(gcs_uri)

    if direction == "upload" and not data_dir.is_dir():
        raise FileNotFoundError(f"Local data directory does not exist: {data_dir}")

    if _have_gcs_library():
        if verbose:
            backend = "google-cloud-storage"
            _log(f"Backend: {backend}")
            _log(f"Local:  {data_dir}")
            _log(f"GCS:    {gcs_uri}")
        return _sync_with_gcs_library(
            data_dir=data_dir,
            gcs_uri=gcs_uri,
            direction=direction,
            verbose=verbose,
        )

    local = str(data_dir).rstrip("/") + "/"
    remote = gcs_uri
    if direction == "upload":
        source, destination = local, remote
    else:
        source, destination = remote, local
        data_dir.mkdir(parents=True, exist_ok=True)

    if verbose:
        _log("Backend: gsutil rsync")
        _log(f"Local:  {data_dir}")
        _log(f"GCS:    {gcs_uri}")

    _run_gsutil_rsync(source=source, destination=destination, verbose=verbose)
    return {"skipped": 0, "transferred": -1, "bytes": -1}


def upload_data(
    data_dir: Optional[os.PathLike[str] | str] = None,
    gcs_uri: Optional[str] = None,
    *,
    verbose: bool = True,
) -> dict[str, int]:
    """Upload local md/data/ to GCS. Skips files that are already identical."""
    target = Path(data_dir) if data_dir is not None else default_data_dir()
    stats = _sync(data_dir=target, gcs_uri=resolve_gcs_uri(gcs_uri), direction="upload", verbose=verbose)
    if verbose:
        if stats["transferred"] >= 0:
            _log(
                f"Done. transferred={stats['transferred']} skipped={stats['skipped']} "
                f"bytes={_human_size(stats['bytes'])}"
            )
        else:
            _log("Done (gsutil rsync).")
    return stats


def download_data(
    data_dir: Optional[os.PathLike[str] | str] = None,
    gcs_uri: Optional[str] = None,
    *,
    verbose: bool = True,
) -> dict[str, int]:
    """Download GCS prefix into local md/data/. Skips files that are already identical."""
    target = Path(data_dir) if data_dir is not None else default_data_dir()
    stats = _sync(data_dir=target, gcs_uri=resolve_gcs_uri(gcs_uri), direction="download", verbose=verbose)
    if verbose:
        if stats["transferred"] >= 0:
            _log(
                f"Done. transferred={stats['transferred']} skipped={stats['skipped']} "
                f"bytes={_human_size(stats['bytes'])}"
            )
        else:
            _log("Done (gsutil rsync).")
    return stats


def setup_notebook_import() -> Path:
    """Add md/ to sys.path so notebooks can ``from tools.gcs_data import ...``."""
    root = md_root()
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    return root


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sync md/data/ with a shared GCS prefix (upload or download)."
    )
    parser.add_argument(
        "--uri",
        default=None,
        help=f"GCS prefix (default: {DEFAULT_GCS_URI!r} or ${ENV_GCS_URI})",
    )
    parser.add_argument(
        "--data-dir",
        default=None,
        help=f"Local data directory (default: {default_data_dir()})",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Print less output",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("upload", help="Upload local data/ to GCS")
    sub.add_parser("download", help="Download GCS prefix to local data/")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    verbose = not args.quiet
    data_dir = Path(args.data_dir) if args.data_dir else default_data_dir()

    try:
        if args.command == "upload":
            upload_data(data_dir=data_dir, gcs_uri=args.uri, verbose=verbose)
        else:
            download_data(data_dir=data_dir, gcs_uri=args.uri, verbose=verbose)
    except subprocess.CalledProcessError as exc:
        print(f"gsutil failed with exit code {exc.returncode}", file=sys.stderr)
        return exc.returncode or 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
