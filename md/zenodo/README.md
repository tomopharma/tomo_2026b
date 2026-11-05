# Zenodo deposit

Tools to publish the MD data (replicates 1–3) as one Zenodo record. `deposit_README.md` becomes the
record's README; `metadata.json` is the record's metadata.

1. **Metadata.** Check the creators in `metadata.json` (name as "Family, Given"; `affiliation` and
   `orcid` optional). The upload script refuses to run while any `TODO` remains.
2. **Build.** `gcloud auth login`, then `./build_deposit.sh`. It downloads from Cloud Storage into
   `~/zenodo_tomo_2026b` (about 23 GB free needed; set `STAGE` to change it) and writes the upload
   set, `README.md` and `MANIFEST.sha256` to `~/zenodo_tomo_2026b/upload`.
3. **Token.** Create a personal access token on zenodo.org (Applications → Personal access tokens,
   scopes `deposit:write` and `deposit:actions`) and save it in `~/.config/zenodo/token` (`chmod 600`).
4. **Rehearse (optional).** With a sandbox.zenodo.org token: `python zenodo_upload.py --sandbox`.
5. **Upload.** `python zenodo_upload.py --dry-run`, then `python zenodo_upload.py`. It creates a draft
   with a reserved DOI, uploads the files (about 11 GB; rerun to resume after an interruption) and
   sets the metadata. It prints the DOI and the draft's web address.
6. **Publish** on the Zenodo web page after checking the draft. Publishing cannot be undone; later
   corrections become a new version with its own DOI.

## New version (code changes only)

The data files carry over from the published record; only `code.zip`, `README.md` and
`MANIFEST.sha256` are replaced.

1. Bump `version` in `metadata.json` and describe the change under "Versions" in `deposit_README.md`.
2. `./new_version.sh <record id>`: stages the three files in `~/zenodo_tomo_2026b_new/upload`,
   reusing the published checksums for the unchanged data files.
3. `python zenodo_upload.py --stage ~/zenodo_tomo_2026b_new --new-version-of <record id>`: creates the
   new-version draft, replaces the three files and sets the metadata. It prints the new DOI.
4. Publish on the Zenodo web page.

Site-specific settings (`GCS_HOME`, cloud project and repository names) go in `md/.local.env`, which is
not version-controlled.
