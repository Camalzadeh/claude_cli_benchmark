#!/usr/bin/env python3
"""Render the two latency graphs as PNG images from results.json."""
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

d = json.load(open("results.json", encoding="utf-8"))
STAGES = ["input_guardrail", "main_agent", "output_guardrail"]
NICE = {"input_guardrail": "Input guardrail", "main_agent": "Main agent", "output_guardrail": "Output guardrail"}

C_COLD, C_TTFT, C_GEN, C_OVER = "#2a78d6", "#eb6834", "#1baf7a", "#b7bcc6"
INK, INK2, MUTED, GRID, SURF = "#0e1116", "#565c65", "#878d97", "#e3e6ea", "#ffffff"
SCALE_MAX = 30000
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11,
    "figure.facecolor": SURF, "axes.facecolor": SURF,
    "text.color": INK, "axes.labelcolor": INK, "axes.edgecolor": GRID,
    "xtick.color": MUTED, "ytick.color": INK,
})

def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else 0.0

def comps_A(name):
    rows = [next(s for s in it["stages"] if s["name"] == name) for it in d["patternA"]]
    cold, ttft, gen = mean([r["cold_start_ms"] for r in rows]), mean([r["ttft_ms"] for r in rows]), mean([r["gen_ms"] for r in rows])
    tot = mean([r["total_ms"] for r in rows])
    over = max(0.0, tot - cold - ttft - gen)
    return dict(cold=cold, ttft=ttft, gen=gen, over=over, total=tot, pts=[r["total_ms"] for r in rows])

def comps_B(name):
    rows = [next(s for s in it["stages"] if s["name"] == name) for it in d["patternB"]]
    ttft, gen = mean([r["ttft_ms"] for r in rows]), mean([r["gen_ms"] for r in rows])
    tot = mean([r["msg_total_ms"] for r in rows])
    over = max(0.0, tot - ttft - gen)
    return dict(cold=0.0, ttft=ttft, gen=gen, over=over, total=tot, pts=[r["msg_total_ms"] for r in rows])

turnA = mean([it["turn_total_ms"] for it in d["patternA"]])
turnB = mean([it["turn_total_ms"] for it in d["patternB"]])
coldB = mean([it["cold_start_ms"] for it in d["patternB"]])
coldB_pts = [it["cold_start_ms"] for it in d["patternB"]]


def draw(ax, rows, title, subtitle):
    """rows: list of (label, comps-dict). Drawn top-to-bottom."""
    n = len(rows)
    ys = list(range(n))[::-1]            # top row highest y
    bh = 0.52
    for y, (label, c) in zip(ys, rows):
        left = 0.0
        for val, col in [(c["cold"], C_COLD), (c["ttft"], C_TTFT), (c["gen"], C_GEN), (c["over"], C_OVER)]:
            if val > 0:
                ax.barh(y, val, left=left, height=bh, color=col, edgecolor=SURF, linewidth=1.4, zorder=2)
                left += val
        # total label at bar end
        ax.text(left + 350, y, f"{c['total']/1000:.1f}s", va="center", ha="left",
                fontsize=10.5, fontweight="bold", color=INK, zorder=5)
        # per-iteration data points, vertically jittered
        pts = c["pts"]
        for i, p in enumerate(pts):
            jitter = (i - (len(pts) - 1) / 2) * (bh / (len(pts))) * 0.9
            ax.scatter(p, y + jitter, s=42, color=INK, edgecolor=SURF, linewidth=1.3, zorder=6, alpha=0.85)

    ax.set_yticks(ys)
    ax.set_yticklabels([r[0] for r in rows], fontsize=10.5)
    ax.set_xlim(0, SCALE_MAX)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_xticks(range(0, SCALE_MAX + 1, 5000))
    ax.set_xticklabels([f"{t//1000}s" for t in range(0, SCALE_MAX + 1, 5000)], fontsize=9.5)
    ax.xaxis.grid(True, color=GRID, linewidth=1, zorder=0)
    ax.set_axisbelow(True)
    for sp in ("top", "right", "left"):
        ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(length=0)
    ax.set_title(title, fontsize=15, fontweight="bold", loc="left", pad=30, color=INK)
    # subtitle at a fixed pixel offset above the axes, independent of axes height
    ax.annotate(subtitle, xy=(0, 1), xycoords="axes fraction", xytext=(0, 8),
                textcoords="offset points", va="bottom", ha="left", fontsize=10.5, color=INK2)


rowsA = [(NICE[s] + "  (haiku)" if s != "main_agent" else NICE[s] + "  (sonnet)", comps_A(s)) for s in STAGES]
rowsB = [("Cold start  (once)", dict(cold=coldB, ttft=0, gen=0, over=0, total=coldB, pts=coldB_pts))] + \
        [(NICE[s] + "  (sonnet · warm)", comps_B(s)) for s in STAGES]

LEG = [
    Patch(fc=C_COLD, label="Cold start (process boot)"),
    Patch(fc=C_TTFT, label="Time to first token"),
    Patch(fc=C_GEN, label="Generation (streaming)"),
    Patch(fc=C_OVER, label="Overhead / glue"),
    Line2D([0], [0], marker="o", color="none", markerfacecolor=INK, markeredgecolor=SURF,
           markeredgewidth=1.3, markersize=8, label="each dot = 1 of 5 iterations"),
]

# ── individual figures ──
for rows, name, title, sub, fn in [
    (rowsA, "A", "Pattern A — three separate processes", f"3 cold spawns · turn mean {turnA/1000:.1f}s · guardrails haiku, main sonnet", "latency_pattern_A.png"),
    (rowsB, "B", "Pattern B — one persistent process", f"1 cold spawn · turn mean {turnB/1000:.1f}s · all stages sonnet (warm)", "latency_pattern_B.png"),
]:
    fig, ax = plt.subplots(figsize=(10, 3.4 if name == "A" else 4.1))
    draw(ax, rows, title, sub)
    ax.set_xlabel("wall-clock per stage (shared 0–30s axis)", fontsize=9.5, color=MUTED)
    fig.legend(handles=LEG, loc="lower center", ncol=3, frameon=False, fontsize=9.5,
               bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=[0, 0.09 if name == "A" else 0.07, 1, 1])
    fig.savefig(fn, dpi=200, bbox_inches="tight", facecolor=SURF)
    print("wrote", fn)
    plt.close(fig)

# ── combined comparison figure (both, shared axis) ──
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 9.0), gridspec_kw={"height_ratios": [3, 4], "hspace": 0.62})
draw(ax1, rowsA, "Pattern A — three separate processes", f"3 cold spawns · turn mean {turnA/1000:.1f}s")
draw(ax2, rowsB, "Pattern B — one persistent process", f"1 cold spawn · turn mean {turnB/1000:.1f}s  →  {round(100*(turnA-turnB)/turnA)}% faster")
ax2.set_xlabel("wall-clock per stage (shared 0–30s axis)", fontsize=9.5, color=MUTED)
fig.suptitle("Where the guardrail pipeline spends its time", fontsize=16, fontweight="bold", x=0.02, ha="left", y=1.0)
fig.legend(handles=LEG, loc="lower center", ncol=5, frameon=False, fontsize=9.5, bbox_to_anchor=(0.5, -0.005))
fig.tight_layout(rect=[0, 0.04, 1, 0.95])
fig.savefig("latency_compare.png", dpi=200, bbox_inches="tight", facecolor=SURF)
print("wrote latency_compare.png")
plt.close(fig)
