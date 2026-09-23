#!/usr/bin/env python3
"""Charts that make backend changes visible, main vs branch, on one scale.

Modes (each takes a "label" file pair per build, usually main then branch):

  spans  Trace waterfall or job timeline. JSON list of spans:
           {"name": "SELECT orders", "start": 12.0, "end": 48.5,
            "lane": "worker-2", "kind": "db"}      (ms; lane and kind optional)
         No lane: one row per span (a waterfall). With lanes: one row per lane
         (a Gantt of jobs, retries, lock holders). kind picks the color.
         --frames DIR also writes frame_%04d.png replaying the timeline with a
         moving "now" line, for gif.sh: requests visibly queuing on main and
         running in parallel on the branch.

  dist   Latency distribution. One number per line (ms). Draws the ECDF of
         each build with p50/p95/p99 marked and listed in the legend.

  series Something over time. CSV with a header, columns: t,value
         (memory during a soak test, queue depth, connections, error rate).
         --band "2,5,dependency down" shades a window, repeatable.

  chart.py spans -o trace.png "main: 41 queries, 380 ms" main.json "this branch: 2 queries, 61 ms" branch.json
  chart.py dist -o latency.png --unit ms "main" main.txt "branch" branch.txt
  chart.py series -o memory.png --ylabel "RSS (MB)" "main" main.csv "branch" branch.csv

Options: --title TEXT, --theme light|dark, --width PX (default 1800, 2x for GitHub),
         --log (dist: log x axis), --unit ms, --ylabel TEXT
Panels in spans mode share one time axis on purpose: a faster branch should
LOOK shorter. Never let each panel autoscale.
"""
import argparse
import csv
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402

# Validated categorical order (dataviz reference palette). Fixed order, never cycled.
SERIES = {
    "light": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"],
    "dark": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9", "#e66767"],
}
THEME = {
    "light": {"bg": "#fcfcfb", "ink": "#0b0b0b", "ink2": "#52514e", "grid": "#e6e5e0", "base": "#9a9994"},
    "dark": {"bg": "#1a1a19", "ink": "#ffffff", "ink2": "#c3c2b7", "grid": "#33332f", "base": "#77766f"},
}


def style(theme):
    t = THEME[theme]
    plt.rcParams.update({
        "figure.facecolor": t["bg"], "axes.facecolor": t["bg"], "savefig.facecolor": t["bg"],
        "axes.edgecolor": t["grid"], "axes.labelcolor": t["ink2"], "text.color": t["ink"],
        "xtick.color": t["ink2"], "ytick.color": t["ink2"], "grid.color": t["grid"],
        "axes.grid": True, "axes.axisbelow": True, "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
        "font.size": 12, "axes.titlesize": 13, "axes.titleweight": "regular", "axes.titlelocation": "left",
        "font.family": ["SF Pro Text", "Helvetica Neue", "Helvetica", "DejaVu Sans"],
    })
    return t


def pairs(values):
    if len(values) % 2:
        sys.exit("expected label/path pairs")
    return list(zip(values[0::2], values[1::2]))


def build_colors(n, args):
    # One build is the baseline and recedes; the change carries the accent.
    t = THEME[args.theme]
    return [t["base"]] + SERIES[args.theme][: n - 1] if n > 1 else SERIES[args.theme][:1]


# ---------- spans ----------

def load_spans(path):
    with open(path) as f:
        spans = json.load(f)
    for s in spans:
        s["start"], s["end"] = float(s["start"]), float(s["end"])
    return spans


def draw_spans(ax, spans, label, kinds, colors, t, xmax, now=None):
    lanes = []
    use_lanes = any("lane" in s for s in spans)
    for s in spans:
        key = s.get("lane") if use_lanes else f"{s['name']}\u0000{len(lanes)}"
        if key not in lanes:
            lanes.append(key)
    for s in spans:
        key = s.get("lane") if use_lanes else None
        row = lanes.index(key) if use_lanes else spans.index(s)
        end = s["end"] if now is None else min(s["end"], now)
        if end <= s["start"]:
            continue
        color = colors[kinds.index(s.get("kind", ""))]
        ax.barh(row, end - s["start"], left=s["start"], height=0.62, color=color, linewidth=0)
        if now is None or now >= s["end"]:
            dur = s["end"] - s["start"]
            text = f"{dur:.0f} ms" if use_lanes else f"{s['name']}  {dur:.0f} ms"
            width = s["end"] - s["start"]
            if use_lanes:
                # Lanes pack spans end to end, so a label outside would sit on
                # the next span: label inside when it fits, otherwise not at all.
                if width > xmax * 0.07:
                    ax.text(s["start"] + xmax / 250, row, text, va="center", ha="left", fontsize=10, color=t["bg"])
                continue
            inside = width > xmax * 0.28
            ax.text(s["start"] + 4 * xmax / 1000 if inside else s["end"] + xmax / 200, row, text,
                    va="center", ha="left", fontsize=10, color=t["bg"] if inside else t["ink2"])
    ax.set_yticks(range(len(lanes)))
    ax.set_yticklabels([str(l) for l in lanes] if use_lanes else ["" for _ in lanes])
    ax.set_ylim(len(lanes) - 0.4, -0.6)
    ax.set_xlim(0, xmax)
    ax.grid(axis="y", visible=False)
    ax.set_title(label, color=t["ink"])
    if now is not None:
        ax.axvline(now, color=t["ink2"], linewidth=1)
    return len(lanes)


def spans_mode(args):
    t = style(args.theme)
    data = [(label, load_spans(path)) for label, path in pairs(args.pairs)]
    xmax = max(s["end"] for _, spans in data for s in spans) * 1.12
    kinds = []
    for _, spans in data:
        for s in spans:
            if s.get("kind", "") not in kinds:
                kinds.append(s.get("kind", ""))
    colors = SERIES[args.theme]
    rows = [len({s.get("lane") for s in spans}) if any("lane" in s for s in spans) else len(spans) for _, spans in data]

    def render(now, path):
        dpi = 150
        heights = [max(1.2, 0.32 * r + 0.8) for r in rows]
        fig, axes = plt.subplots(len(data), 1, figsize=(args.width / dpi, sum(heights)), dpi=dpi,
                                 gridspec_kw={"height_ratios": heights}, squeeze=False, sharex=True)
        for ax, (label, spans) in zip(axes[:, 0], data):
            draw_spans(ax, spans, label, kinds, colors, t, xmax, now)
        axes[-1, 0].set_xlabel("ms")
        if any(kinds) and len(kinds) > 1:
            handles = [plt.Rectangle((0, 0), 1, 1, color=colors[i]) for i in range(len(kinds))]
            fig.legend(handles, kinds, loc="upper right", ncol=len(kinds), frameon=False, fontsize=10)
        if args.title:
            fig.suptitle(args.title, x=0.01, ha="left", color=t["ink"])
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)

    render(None, args.out)
    print(args.out)
    if args.frames:
        os.makedirs(args.frames, exist_ok=True)
        n = args.frame_count
        for i in range(n + 1):
            render(xmax * i / n, os.path.join(args.frames, f"frame_{i:04d}.png"))
        print(f"{args.frames}: {n + 1} frames")


# ---------- dist ----------

def pct(sorted_vals, p):
    k = (len(sorted_vals) - 1) * p
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def dist_mode(args):
    t = style(args.theme)
    data = []
    for label, path in pairs(args.pairs):
        with open(path) as f:
            vals = sorted(float(x) for x in f if x.strip())
        data.append((label, vals))
    colors = build_colors(len(data), args)
    fig, ax = plt.subplots(figsize=(args.width / 150, 5.2), dpi=150)
    for (label, vals), color in zip(data, colors):
        n = len(vals)
        ys = [(i + 1) / n for i in range(n)]
        p50, p95, p99 = (pct(vals, p) for p in (0.5, 0.95, 0.99))
        ax.step(vals, ys, where="post", color=color, linewidth=2,
                label=f"{label}   p50 {p50:.0f}  p95 {p95:.0f}  p99 {p99:.0f} {args.unit}  (n={n})")
        for p, v in ((0.5, p50), (0.95, p95), (0.99, p99)):
            ax.plot([v], [p], "o", color=color, markersize=8, markeredgecolor=t["bg"], markeredgewidth=2)
    if args.log:
        ax.set_xscale("log")
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set_xlabel(f"latency ({args.unit})")
    ax.set_ylabel("share of requests at or below")
    ax.set_ylim(0, 1.02)
    ax.legend(loc="lower right", frameon=False)
    ax.set_title(args.title or "Latency, cumulative", color=t["ink"])
    fig.tight_layout()
    fig.savefig(args.out)
    print(args.out)


# ---------- series ----------

def series_mode(args):
    t = style(args.theme)
    data = []
    for label, path in pairs(args.pairs):
        with open(path) as f:
            rows = list(csv.DictReader(f))
        data.append((label, [float(r["t"]) for r in rows], [float(r["value"]) for r in rows]))
    colors = build_colors(len(data), args)
    fig, ax = plt.subplots(figsize=(args.width / 150, 4.6), dpi=150)
    for band in args.band or []:
        start, end, *text = band.split(",", 2)
        ax.axvspan(float(start), float(end), color=t["grid"], alpha=0.8, linewidth=0)
        if text:
            ax.text(float(start), 1.0, " " + text[0], transform=ax.get_xaxis_transform(),
                    va="top", ha="left", fontsize=10, color=t["ink2"])
    span = (max(max(d[2]) for d in data) - min(min(d[2]) for d in data)) or 1
    placed = []
    for (label, xs, ys), color in zip(data, colors):
        ax.plot(xs, ys, color=color, linewidth=2, label=label)
        # Direct end label, unless it would sit on another one (the legend still names it).
        if all(abs(ys[-1] - y) > span * 0.06 for y in placed):
            placed.append(ys[-1])
            ax.annotate(f"{label}: {ys[-1]:g}", (xs[-1], ys[-1]), xytext=(6, 0), textcoords="offset points",
                        va="center", fontsize=10, color=t["ink2"])
    ax.set_xlabel(args.xlabel)
    ax.set_ylabel(args.ylabel)
    ax.legend(loc="upper left", frameon=False)
    ax.set_title(args.title or "", color=t["ink"])
    fig.tight_layout()
    fig.savefig(args.out)
    print(args.out)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("mode", choices=["spans", "dist", "series"])
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--title")
    p.add_argument("--theme", choices=["light", "dark"], default="light")
    p.add_argument("--width", type=int, default=1800)
    p.add_argument("--log", action="store_true")
    p.add_argument("--unit", default="ms")
    p.add_argument("--xlabel", default="seconds")
    p.add_argument("--ylabel", default="")
    p.add_argument("--band", action="append", help='series: shade a window, "start,end,label" (e.g. a fault)')
    p.add_argument("--frames", help="spans: also write a replay, frame_%%04d.png, to this directory")
    p.add_argument("--frame-count", type=int, default=90)
    p.add_argument("pairs", nargs="+", help='"label" path, repeated (baseline first)')
    args = p.parse_args()
    {"spans": spans_mode, "dist": dist_mode, "series": series_mode}[args.mode](args)


if __name__ == "__main__":
    main()
