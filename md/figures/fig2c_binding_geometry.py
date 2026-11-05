#!/usr/bin/env python3
"""Figure 2c: calx-β RMSD from the docked pose and fraction of docked contacts (Q) over 100 ns.

Reads md1's per-frame binding metrics (rep{n}/md_binding_metrics.csv) and plots 2 ns block
averages for every replicate, replicate 2 highlighted, as in the SI binding-geometry chart (S5).

Usage:
    python fig2c_binding_geometry.py --metrics-dir ../data/md_calx_3qqu_full --out-dir out/

Writes fig2c_binding_geometry.{pdf,svg} (vector) and .{png,tif} (600 dpi) in --out-dir.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

BLOCK_NS = 2.0
HIGHLIGHT = 2  # replicate that shifts furthest (75–90 ns)
WIDTH_CM, HEIGHT_CM = 17.0, 6.0  # MDPI full text width
ACCENT, GREY = "#1f6fb4", "#8c8c8c"
STYLE = {1: (GREY, 0.95, 1.1), 2: (ACCENT, 1.0, 1.6), 3: (GREY, 0.5, 1.1)}  # colour, alpha, line width

plt.rcParams.update({
    "font.family": "Arial", "font.size": 8, "axes.linewidth": 0.6,
    "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
    "svg.fonttype": "none", "pdf.fonttype": 42,  # editable text in vector output
})


def block_means(csv: Path) -> pd.DataFrame:
    """2 ns block averages of RMSD (receptor fit) and Q, centred on each block."""
    d = pd.read_csv(csv)
    ns = d["time_ps"] / 1000.0
    block = np.minimum((ns // BLOCK_NS).astype(int), int(ns.max() // BLOCK_NS) - 1)
    return d.assign(ns=ns, block=block).groupby("block").agg(
        ns=("ns", "mean"), rmsd=("calx_rmsd_receptor_fit_nm", "mean"), q=("q_native", "mean"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--metrics-dir", type=Path, required=True, help="folder holding rep1/, rep2/, rep3/")
    parser.add_argument("--out-dir", type=Path, default=Path("."))
    parser.add_argument("--reps", type=int, nargs="+", default=[1, 2, 3])
    parser.add_argument("--label", default="c", help="panel letter; empty string for none")
    args = parser.parse_args()

    data = {r: block_means(args.metrics_dir / f"rep{r}" / "md_binding_metrics.csv") for r in args.reps}

    cm = 1 / 2.54
    fig, (ax_r, ax_q) = plt.subplots(1, 2, figsize=(WIDTH_CM * cm, HEIGHT_CM * cm))
    # Draw the highlighted replicate last so it sits on top.
    for r in sorted(args.reps, key=lambda r: r == HIGHLIGHT):
        colour, alpha, lw = STYLE.get(r, (GREY, 0.7, 1.1))
        b = data[r]
        ax_r.plot(b["ns"], b["rmsd"], color=colour, alpha=alpha, lw=lw, label=f"Simulation {r}")
        ax_q.plot(b["ns"], b["q"], color=colour, alpha=alpha, lw=lw)

    ax_r.set(ylim=(0, 1.6), ylabel="calx-β RMSD from docked pose (nm)")
    ax_q.set(ylim=(0, 1.0), ylabel="Fraction of docked contacts kept (Q)")
    for ax in (ax_r, ax_q):
        ax.set(xlim=(0, 100), xlabel="Time (ns)", xticks=range(0, 101, 25))
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e3e3e3", lw=0.5)
        ax.set_axisbelow(True)
    handles, labels = ax_r.get_legend_handles_labels()
    order = sorted(range(len(labels)), key=lambda i: labels[i])
    fig.legend([handles[i] for i in order], [labels[i] for i in order], loc="upper center",
               ncol=len(labels), frameon=False, bbox_to_anchor=(0.5, 1.0), handlelength=1.8)
    if args.label:
        fig.text(0.005, 0.98, args.label, fontsize=11, fontweight="bold", va="top")
    fig.tight_layout(rect=(0.015, 0, 1, 0.9), w_pad=2.5)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.out_dir / "fig2c_binding_geometry"
    for ext in ("pdf", "svg"):
        fig.savefig(f"{stem}.{ext}")
    for ext in ("png", "tif"):
        fig.savefig(f"{stem}.{ext}", dpi=600, **({"pil_kwargs": {"compression": "tiff_lzw"}} if ext == "tif" else {}))
    for r, b in data.items():
        late = b[b["ns"] >= 75]
        print(f"simulation {r}: {len(b)} blocks; peak RMSD {b['rmsd'].max():.2f} nm; "
              f"min Q {b['q'].min():.2f}; last block RMSD {b['rmsd'].iloc[-1]:.2f}, Q {b['q'].iloc[-1]:.2f}; "
              f"75-100 ns mean Q {late['q'].mean():.2f}")
    print(f"Wrote {stem}.pdf/.svg/.png/.tif")


if __name__ == "__main__":
    main()
