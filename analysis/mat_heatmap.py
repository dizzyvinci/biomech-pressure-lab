#!/usr/bin/env python3
"""
mat_heatmap.py — turn the coarse Velostat matrix into a clean plantar pressure map.

The pressure_mat.ino firmware streams one frame per line: `t_ms,c0,c1,...` (row-major,
N_ROWS*N_COLS ADC values). A raw 8x11 grid is blocky, but you don't need more cells to *see*
the hot region — bicubic-interpolate it up. It's the standard, free resolution hack: bicubic
matches linear on error (RMSE ~0.089) and reads far cleaner than nearest-neighbor. See
docs/maker_hacks.md.

    # from a capture file (each line = t_ms,v0,v1,...  row-major)
    python mat_heatmap.py --input frames.csv --rows 8 --cols 11 --out map.png

    # no hardware yet? synthesize a footprint and render it
    python mat_heatmap.py --demo --out demo_map.png

--agg peak = the max each cell saw (a peak-pressure map); --agg mean = time-average.
Values are raw ADC (this is a spatial/visual tool); calibrate per-cell for real kPa.
"""
import argparse
import numpy as np


def load_frames(path, rows, cols):
    n = rows * cols
    grids = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(",")
            vals = parts[1:] if len(parts) == n + 1 else parts   # drop leading t_ms if present
            try:
                arr = np.array([float(v) for v in vals], dtype=float)
            except ValueError:
                continue
            if arr.size == n:
                grids.append(arr.reshape(rows, cols))
    if not grids:
        raise SystemExit(f"no valid {rows}x{cols} frames parsed from {path} — check --rows/--cols")
    return np.stack(grids)


def demo_grid(rows=24, cols=10):
    """Synthesize a plausible plantar footprint (heel + met ridge + hallux) on a foot mask."""
    yy, xx = np.mgrid[0:rows, 0:cols]
    cy = cols / 2.0 - 0.5

    def blob(r0, c0, sr, sc, amp):
        return amp * np.exp(-(((yy - r0) / sr) ** 2 + ((xx - c0) / sc) ** 2))

    g  = blob(rows * 0.14, cy,               rows * 0.09, cols * 0.34, 780)   # heel
    g += blob(rows * 0.70, cy,               rows * 0.10, cols * 0.42, 520)   # met heads ridge
    g += blob(rows * 0.72, cy - cols * 0.30, rows * 0.06, cols * 0.16, 640)   # met1
    g += blob(rows * 0.90, cy - cols * 0.26, rows * 0.05, cols * 0.12, 700)   # hallux
    g += blob(rows * 0.42, cy + cols * 0.06, rows * 0.15, cols * 0.20, 120)   # low lateral arch
    # foot-shaped mask: narrow at the heel, wider at the forefoot
    half = 0.32 + 0.55 * np.clip(yy / max(rows - 1, 1), 0, 1)
    g = g * (np.abs(xx - cy) / (cols / 2.0) < half)
    return g[None, ...]


def main():
    ap = argparse.ArgumentParser(description="Bicubic heatmap of a coarse Velostat pressure matrix.")
    ap.add_argument("--input", help="capture file: lines of t_ms,v0,v1,... (row-major)")
    ap.add_argument("--demo", action="store_true", help="synthesize a footprint instead")
    ap.add_argument("--rows", type=int, default=24, help="matrix rows (heel->toe)")
    ap.add_argument("--cols", type=int, default=10, help="matrix cols (medial->lateral)")
    ap.add_argument("--agg", choices=["peak", "mean"], default="peak")
    ap.add_argument("--interp", default="bicubic", help="matplotlib interpolation (bicubic/bilinear/nearest)")
    ap.add_argument("--out", default="mat_map.png")
    a = ap.parse_args()

    if a.demo:
        frames = demo_grid(a.rows, a.cols)
    elif a.input:
        frames = load_frames(a.input, a.rows, a.cols)
    else:
        raise SystemExit("pass --input frames.csv (with --rows/--cols) or --demo")
    rows, cols = frames.shape[1], frames.shape[2]

    grid = frames.max(axis=0) if a.agg == "peak" else frames.mean(axis=0)

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(cols * 0.34 + 2, rows * 0.22 + 1.4))
    try:
        im = ax.imshow(grid, cmap="turbo", interpolation=a.interp, origin="lower", aspect="auto")
    except ValueError:
        im = ax.imshow(grid, cmap="jet", interpolation=a.interp, origin="lower", aspect="auto")
    pr, pc = np.unravel_index(int(np.argmax(grid)), grid.shape)
    ax.plot(pc, pr, "o", ms=8, mfc="none", mec="white", mew=1.6)     # mark the peak cell
    ax.set_title(f"plantar pressure — {rows}x{cols} cells, {a.interp} ({a.agg})", fontsize=10)
    ax.set_xticks([]); ax.set_yticks([])
    cb = fig.colorbar(im, ax=ax, shrink=0.85); cb.set_label("ADC (raw)", fontsize=8)
    ax.text(0.5, -0.03, "bicubic-interpolated coarse matrix — docs/maker_hacks.md",
            transform=ax.transAxes, ha="center", va="top", fontsize=7, color="#64748b")
    fig.tight_layout()
    fig.savefig(a.out, dpi=130)
    print(f"-> {a.out}  (peak cell r{pr} c{pc} = {grid[pr, pc]:.0f} ADC, {frames.shape[0]} frame(s))")


if __name__ == "__main__":
    main()
