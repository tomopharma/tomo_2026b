# tomo_2026b: Molecular Dynamics with GROMACS — publication workflows

Dockerized Jupyter stacks for the 2026-b paper artifacts:

| Stack | Script | Port | Image |
| --- | --- | --- | --- |
| **MD (CPU)** | [`./md-run.sh`](md-run.sh) | **8890** (`MD_PORT`) | `tomo_2026b_md` — `gromacs=2025.4=nompi*` |
| **MD (GPU)** | [`./md-run.sh --gpu`](md-run.sh) | **8891** (`MD_GPU_PORT`) | `tomo_2026b_md_gpu` — `gromacs=2025.4=nompi_cuda*` |

Notebooks live in [`md/notebooks/`](md/notebooks/). Both images mount the same `notebooks/` and `data/` trees.

The script starts the container detached, waits until the port accepts connections, **opens your browser**, then streams logs (Ctrl+C stops log follow only).

```bash
# CPU (Apple Silicon or Linux; default)
./md-run.sh --build
./md-run.sh

# GPU (linux/amd64 host with NVIDIA driver + NVIDIA Container Toolkit)
./md-run.sh --gpu --build
./md-run.sh --gpu
```

## Layout

```text
tomo_2026b/
├── md-run.sh               # wrapper → md/up-md.sh
└── md/
    ├── docker-compose.yml  # services md (default) and md-gpu (profile gpu)
    ├── up-md.sh
    ├── deploy-to-gcp.sh
    ├── container/
    │   ├── Dockerfile + environment.yml           # CPU
    │   ├── Dockerfile.gpu + environment-gpu.yml   # CUDA
    │   ├── start.sh
    │   └── jupyter_notebook_config.py
    ├── notebooks/
    └── data/               # local only (gitignored): docking inputs and MD outputs
```

### CPU vs GPU images

Use the **CPU** image for local Jupyter, nglview, short tests, and MM-GBSA. Use the **GPU** image only for production `mdrun` on a Linux NVIDIA machine. Do not `--gpu` on a Mac: conda-forge CUDA GROMACS is **linux-64** only.

After changing `md/container/environment.yml` or `environment-gpu.yml`:

```bash
./md-run.sh --build          # CPU
./md-run.sh --gpu --build    # GPU
```

On **Apple Silicon**, the CPU image builds for **arm64** natively. The GPU image is always **linux/amd64**.

On the GPU container, confirm offload:

```bash
docker compose --profile gpu exec md-gpu nvidia-smi
docker compose --profile gpu exec md-gpu gmx --version   # should mention CUDA / GPU
```

## Manual compose

```bash
docker compose up -d md                              # http://127.0.0.1:8890
docker compose --profile gpu up -d md-gpu            # http://127.0.0.1:8891
docker compose --profile gpu down
```
