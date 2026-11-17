"""Benchmarks for the report.  Run:  python3 benchmark.py

Produces results.json and figures/*.png.  Everything is seeded, so the
comparison counts are exactly reproducible; wall-clock times vary a little
between machines but the ordering and trends do not.
"""
import json
import os
import random
import statistics
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import pydoc_data.topics as _topics

import selection
from string_matching import ALGORITHMS

random.seed(2026)
os.makedirs("figures", exist_ok=True)
RESULTS = {}

STR_ORDER = ["brute_force", "rabin_karp", "kmp", "boyer_moore", "quick_search"]
LABEL = {"brute_force": "Brute force", "rabin_karp": "Rabin-Karp", "kmp": "KMP",
         "boyer_moore": "Boyer-Moore", "quick_search": "Quick Search"}
COLOR = {"brute_force": "#8c8c8c", "rabin_karp": "#d98e04", "kmp": "#2b8a8a",
         "boyer_moore": "#4c6ef5", "quick_search": "#d6336c"}

plt.rcParams.update({"font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": 0.25, "figure.dpi": 200})


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
def best_time(f, *args, repeat=3):
    best = float("inf")
    for _ in range(repeat):
        t0 = time.perf_counter()
        f(*args)
        best = min(best, time.perf_counter() - t0)
    return best


def counts(f, text, pat):
    stats = {}
    hits = f(text, pat, stats)
    return stats, hits


def make_texts(n):
    english_src = "".join(_topics.topics.values())          # real English documentation
    english = (english_src * (n // len(english_src) + 1))[:n]
    return {
        "Binary (2)": "".join(random.choice("01") for _ in range(n)),
        "DNA (4)": "".join(random.choice("ACGT") for _ in range(n)),
        "English text (~90)": english,
        "Random ASCII (95)": "".join(chr(random.randint(32, 126)) for _ in range(n)),
    }


def sample_patterns(text, m, how_many=5):
    return [text[i:i + m] for i in
            (random.randint(0, len(text) - m) for _ in range(how_many))]


def thousands(ax):
    """Show 160000 as 160k on the x axis."""
    ax.xaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda v, _: f"{v / 1000:g}k"))


def save(fig, name, rect=None):
    fig.tight_layout(rect=rect)
    fig.savefig(f"figures/{name}.png")
    plt.close(fig)


# --------------------------------------------------------------------------
# A. Effect of alphabet size  (n = 300k, m = 8)
# --------------------------------------------------------------------------
def exp_alphabet(n=300_000, m=8, cached=None):
    if cached:                                            # re-plot from results.json
        n, m, res = cached["n"], cached["m"], cached["data"]
    else:
        texts = make_texts(n)
        res = {}
        for tname, text in texts.items():
            pats = sample_patterns(text, m)
            res[tname] = {}
            for a in STR_ORDER:
                f = ALGORITHMS[a]
                t = statistics.mean(best_time(f, text, p) for p in pats)
                c = statistics.mean(counts(f, text, p)[0].get("cmp", 0) for p in pats) / n
                res[tname][a] = {"time_ms": t * 1000, "cmp_per_char": c}
        RESULTS["alphabet"] = {"n": n, "m": m, "data": res}

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.3))
    names = list(res)
    w = 0.16
    for k, a in enumerate(STR_ORDER):
        xs = [i + (k - 2) * w for i in range(len(names))]
        axes[0].bar(xs, [res[t][a]["time_ms"] for t in names], w,
                    label=LABEL[a], color=COLOR[a])
        axes[1].bar(xs, [res[t][a]["cmp_per_char"] for t in names], w,
                    color=COLOR[a])
    for ax in axes:
        ax.set_xticks(range(len(names)))
        ax.set_xticklabels([t.replace(" (", "\n(") for t in names], fontsize=7)
    axes[0].set_ylabel("Time (ms)")
    axes[0].set_title(f"Running time (n={n:,}, m={m})", fontsize=9)
    axes[1].set_ylabel("Comparisons per text character")
    axes[1].set_title("Character comparisons", fontsize=9)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=5, frameon=False, fontsize=7.5)
    save(fig, "fig_alphabet", rect=(0, 0.07, 1, 1))


# --------------------------------------------------------------------------
# B. Effect of pattern length on English text
# --------------------------------------------------------------------------
def exp_pattern_length(n=300_000, lengths=(2, 4, 8, 16, 32, 64), cached=None):
    if cached:                                            # re-plot from results.json
        n, lengths, res = cached["n"], tuple(cached["lengths"]), cached["data"]
    else:
        text = make_texts(n)["English text (~90)"]
        res = {a: {"time_ms": [], "cmp_per_char": []} for a in STR_ORDER}
        for m in lengths:
            pats = sample_patterns(text, m)
            for a in STR_ORDER:
                f = ALGORITHMS[a]
                res[a]["time_ms"].append(
                    statistics.mean(best_time(f, text, p, repeat=2) for p in pats) * 1000)
                res[a]["cmp_per_char"].append(
                    statistics.mean(counts(f, text, p)[0].get("cmp", 0) for p in pats) / n)
        RESULTS["pattern_length"] = {"n": n, "lengths": list(lengths), "data": res}

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))
    for a in STR_ORDER:
        axes[0].plot(lengths, res[a]["time_ms"], marker="o", ms=3,
                     label=LABEL[a], color=COLOR[a])
        axes[1].plot(lengths, res[a]["cmp_per_char"], marker="o", ms=3,
                     color=COLOR[a])
    for ax in axes:
        ax.set_xscale("log", base=2)
        ax.set_xticks(lengths)
        ax.set_xticklabels(lengths)
        ax.set_xlabel("Pattern length m")
    axes[0].set_ylabel("Time (ms)")
    axes[0].set_title("Running time on English text", fontsize=9)
    axes[1].set_ylabel("Comparisons per text character")
    axes[1].set_title("Character comparisons", fontsize=9)
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=5, frameon=False, fontsize=7.5)
    save(fig, "fig_pattern_length", rect=(0, 0.07, 1, 1))


# --------------------------------------------------------------------------
# C. Scaling with text length (English, m = 8)
# --------------------------------------------------------------------------
def exp_text_scaling(sizes=(35_000, 70_000, 140_000, 280_000, 560_000), m=8):
    src = "".join(_topics.topics.values())
    res = {a: [] for a in STR_ORDER}
    for n in sizes:
        text = src[:n]
        pats = sample_patterns(text, m)
        for a in STR_ORDER:
            res[a].append(statistics.mean(
                best_time(ALGORITHMS[a], text, p, repeat=2) for p in pats) * 1000)
    RESULTS["text_scaling"] = {"sizes": list(sizes), "m": m, "data": res}

    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    for a in STR_ORDER:
        ax.plot(sizes, res[a], marker="o", ms=3, label=LABEL[a], color=COLOR[a])
    thousands(ax)
    ax.set_xlabel("Text length n (characters)")
    ax.set_ylabel("Time (ms)")
    ax.set_title(f"Running time grows linearly with n (m={m})", fontsize=9)
    ax.legend(fontsize=7, frameon=False)
    save(fig, "fig_text_scaling")


# --------------------------------------------------------------------------
# D. Worst cases (comparison counts, n = 20,000, m = 100)
# --------------------------------------------------------------------------
def exp_worst_case(n=20_000, m=100):
    cases = {
        "a^n / a^(m-1)b": ("a" * n, "a" * (m - 1) + "b"),
        "a^n / b a^(m-1)": ("a" * n, "b" + "a" * (m - 1)),
        "a^n / a^m": ("a" * n, "a" * m),
        "random DNA / random": ("".join(random.choice("ACGT") for _ in range(n)),
                                "".join(random.choice("ACGT") for _ in range(m))),
    }
    res = {}
    for cname, (t, p) in cases.items():
        res[cname] = {a: counts(ALGORITHMS[a], t, p)[0].get("cmp", 0) / n
                      for a in STR_ORDER}
    RESULTS["worst_case"] = {"n": n, "m": m, "data": res}

    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    names = list(res)
    w = 0.16
    floor = 0.05                                          # bars for ~0 are drawn here
    for k, a in enumerate(STR_ORDER):
        xs = [i + (k - 2) * w for i in range(len(names))]
        ax.bar(xs, [max(res[c][a], floor) for c in names], w,
               label=LABEL[a], color=COLOR[a])
        for x, c in zip(xs, names):
            if res[c][a] < floor:
                ax.text(x, floor * 1.15, "~0", ha="center", va="bottom", fontsize=6)
    ax.set_yscale("log")
    ax.set_ylim(floor, 300)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=7.5)
    ax.set_ylabel("Comparisons per text character (log)")
    ax.set_title(f"Adversarial inputs (n={n:,}, m={m})", fontsize=9)
    ax.legend(fontsize=7, frameon=False, ncol=5, loc="upper center",
              bbox_to_anchor=(0.5, -0.12))
    save(fig, "fig_worst_case")


# --------------------------------------------------------------------------
# E. Quick Search - average shift length per window
# --------------------------------------------------------------------------
def exp_quick_search_shift(n=200_000, lengths=(2, 4, 8, 16, 32, 64)):
    texts = make_texts(n)
    res = {}
    for tname, text in texts.items():
        res[tname] = []
        for m in lengths:
            shifts, cmps = [], []
            for p in sample_patterns(text, m):
                s, _ = counts(ALGORITHMS["quick_search"], text, p)
                shifts.append(n / s["windows"])
                cmps.append(s["cmp"] / s["windows"])
            res[tname].append({"m": m, "avg_shift": statistics.mean(shifts),
                               "cmp_per_window": statistics.mean(cmps)})
    RESULTS["quick_search_shift"] = {"n": n, "lengths": list(lengths), "data": res}

    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    for tname, rows in res.items():
        ax.plot(lengths, [r["avg_shift"] for r in rows], marker="o", ms=3, label=tname)
    ax.plot(lengths, [m + 1 for m in lengths], "k--", lw=0.8, label="Maximum shift m+1")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log", base=2)
    ax.set_xticks(lengths)
    ax.set_xticklabels(lengths)
    ax.set_xlabel("Pattern length m")
    ax.set_ylabel("Average shift per window")
    ax.set_title("Quick Search: average shift", fontsize=9)
    ax.legend(fontsize=7, frameon=False)
    save(fig, "fig_qs_shift")


# --------------------------------------------------------------------------
# F. Selection
# --------------------------------------------------------------------------
def exp_selection(sizes=(10_000, 20_000, 40_000, 80_000, 160_000, 320_000, 640_000)):
    algos = {"Quickselect": selection.quickselect,
             "Median of medians": selection.median_of_medians_select,
             "Sort then index": selection.sort_select}
    res = {n: {} for n in sizes}
    work = {"Quickselect": [], "Median of medians": []}
    for n in sizes:
        a = [random.random() for _ in range(n)]
        k = n // 2
        for name, f in algos.items():
            res[n][name] = best_time(f, a, k, repeat=3) * 1000
        for name in work:
            runs = 30 if name == "Quickselect" else 1     # quickselect is randomized
            total = 0
            for _ in range(runs):
                st = {}
                algos[name](a, k, st)
                total += st["work"]
            work[name].append(total / runs / n)
    RESULTS["selection_scaling"] = {"sizes": list(sizes), "time_ms": res,
                                    "work_per_n": work}

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))
    cols = {"Quickselect": "#d6336c", "Median of medians": "#4c6ef5",
            "Sort then index": "#8c8c8c"}
    for name in algos:
        axes[0].plot(sizes, [res[n][name] for n in sizes], marker="o", ms=3,
                     label=name, color=cols[name])
    axes[0].set_xlabel("List size n")
    axes[0].set_ylabel("Time (ms)")
    axes[0].set_title("Finding the median", fontsize=9)
    axes[0].legend(fontsize=7, frameon=False)
    for name, w in work.items():
        axes[1].plot(sizes, w, marker="o", ms=3, label=name, color=cols[name])
    axes[1].set_xlabel("List size n")
    axes[1].set_ylabel("Elements scanned / n")
    axes[1].set_title("Scan work per element (quickselect: mean of 30 runs)", fontsize=8.5)
    for ax in axes:
        thousands(ax)
    axes[1].set_ylim(bottom=0)
    axes[1].legend(fontsize=7, frameon=False)
    save(fig, "fig_selection_scaling")

    # input shapes
    n = 200_000
    shapes = {
        "random": [random.random() for _ in range(n)],
        "sorted": list(range(n)),
        "reverse sorted": list(range(n, 0, -1)),
        "all equal": [7] * n,
        "10 distinct values": [random.randint(0, 9) for _ in range(n)],
    }
    shape_res = {}
    for sname, a in shapes.items():
        shape_res[sname] = {}
        for name, f in algos.items():
            shape_res[sname][name] = best_time(f, a, n // 2, repeat=3) * 1000
    RESULTS["selection_shapes"] = {"n": n, "data": shape_res}

    # quickselect run-time variability
    a = [random.random() for _ in range(100_000)]
    runs = []
    for _ in range(60):
        t0 = time.perf_counter()
        selection.quickselect(a, 50_000)
        runs.append((time.perf_counter() - t0) * 1000)
    mom_t = best_time(selection.median_of_medians_select, a, 50_000) * 1000
    RESULTS["quickselect_variance"] = {
        "n": 100_000, "runs": len(runs), "min": min(runs), "median": statistics.median(runs),
        "max": max(runs), "stdev": statistics.stdev(runs), "mom_ms": mom_t}

    fig, ax = plt.subplots(figsize=(5.2, 3.0))
    ax.hist(runs, bins=15, color="#d6336c", alpha=0.85)
    ax.axvline(mom_t, color="#4c6ef5", ls="--", lw=1.2, label="Median of medians")
    ax.set_xlabel("Quickselect running time (ms), 60 runs, n=100,000")
    ax.set_ylabel("Runs")
    ax.set_title("Randomized pivots: time varies from run to run", fontsize=9)
    ax.legend(fontsize=7, frameon=False)
    save(fig, "fig_quickselect_variance")


if __name__ == "__main__":
    import sys
    if "--replot" in sys.argv:                            # redraw two charts from saved data
        saved = json.load(open("results.json"))
        exp_alphabet(cached=saved["alphabet"])
        exp_pattern_length(cached=saved["pattern_length"])
        print("re-plotted fig_alphabet.png and fig_pattern_length.png from results.json")
        sys.exit(0)
    for fn in (exp_alphabet, exp_pattern_length, exp_text_scaling, exp_worst_case,
               exp_quick_search_shift, exp_selection):
        t0 = time.perf_counter()
        fn()
        print(f"{fn.__name__:<24} done in {time.perf_counter() - t0:5.1f}s")
    with open("results.json", "w") as f:
        json.dump(RESULTS, f, indent=1)
    print("wrote results.json and figures/")
