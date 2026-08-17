"""Jupyter config for the tomo_2026b MD image when it runs as an Ephemeral tenant app.

This file is not GROMACS/CUDA settings. It makes the same Docker image work
behind Sarno Ephemeral: Cloud Run gateway → per-session VM → Jupyter on :8888.

Loaded by container/start.sh (image CMD). Local docker-compose.yml overrides
CMD with a bare ``jupyter notebook`` line, so ./md-run.sh does not use this
file. Cloud/GCE catalog launches do.

Public URLs are a session prefix (e.g. https://<gateway>/s/<session-id>/),
not /. JUPYTER_BASE_URL must match that prefix or the UI requests /static and
/api on the gateway origin and 404s.

Env (set by vm-runtime launch-app.sh):
  WORKSPACE_DIR       notebook root (default /workspace)
  COMPANY_SHARED_DIR  optional /shared mount; symlink workspace/shared → it
  JUPYTER_BASE_URL    gateway path prefix (trailing slash added if missing)
  JUPYTER_TOKEN       session token; empty password (token-only)

Also: listen on 0.0.0.0, no browser, allow root, trust X-Forwarded-* so
links/websockets use the gateway URL. allow_origin=* and disable_check_xsrf
are required because the browser Origin is Cloud Run while Jupyter Host is
the VM IP — Jupyter then reports CORS failures as HTTP 404. Those flags
weaken CSRF; they are for gateway+token sessions, not public notebooks.

Sibling of ephemeral-vm apps/jupyter-app/jupyter_server_config.py (same
contract so this GROMACS image can be listed as a tenant notebook app).
"""
import os

c = get_config()  # noqa: F821

_work = os.environ.get("WORKSPACE_DIR", "/workspace").strip() or "/workspace"
_root = _work

_shared = os.environ.get("COMPANY_SHARED_DIR", "/shared").strip() or "/shared"
_link = os.path.join(_work, "shared")
if os.path.isdir(_shared) and not os.path.lexists(_link):
    try:
        os.symlink(_shared, _link)
    except OSError:
        pass

_base = os.environ.get("JUPYTER_BASE_URL", "").strip()
if _base and not _base.endswith("/"):
    _base = f"{_base}/"

_token = os.environ.get("JUPYTER_TOKEN", "").strip()


def _apply(app) -> None:
    app.ip = "0.0.0.0"
    app.open_browser = False
    app.allow_remote_access = True
    app.allow_root = True
    if hasattr(app, "trust_xheaders"):
        app.trust_xheaders = True
    # Browser Origin is the Cloud Run gateway; Jupyter Host is the VM IP.
    # Jupyter reports CORS failures as HTTP 404 "Not Found".
    if hasattr(app, "allow_origin"):
        app.allow_origin = "*"
    if hasattr(app, "disable_check_xsrf"):
        app.disable_check_xsrf = True
    if hasattr(app, "root_dir"):
        app.root_dir = _root
    if hasattr(app, "notebook_dir"):
        app.notebook_dir = _root
    if _base:
        app.base_url = _base
    app.token = _token
    app.password = ""


_apply(c.ServerApp)
_apply(c.NotebookApp)
try:
    c.IdentityProvider.token = _token
except Exception:
    pass
