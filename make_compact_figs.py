"""Compact multi-panel figures for the short report (drawn from results.json,
so nothing is re-measured).  Run:  python3 make_compact_figs.py
Writes figures/fig_c_selection.png and figures/fig_c_strings.png."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

R = json.load(open("results.json"))
STR = ["brute_force", "rabin_karp", "kmp", "boyer_moore", "quick_search"]
LBL = {"brute_force": "Brute force", "rabin_karp": "Rabin-Karp", "kmp": "KMP",
       "boyer_moore": "Boyer-Moore", "quick_search": "Quick Search"}
COL = {"brute_force": "#8c8c8c", "rabin_karp": "#d98e04", "kmp": "#2b8a8a",
       "boyer_moore": "#4c6ef5", "quick_search": "#d6336c"}
plt.rcParams.update({"font.size": 7, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.25, "figure.dpi": 220,
                     "axes.titlesize": 7.5, "axes.titleweight": "bold"})


def kfmt(ax):
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v / 1000:g}k"))


# ------------------------------------------------------------------ selection
def selection_fig():
    S = R["selection_scaling"]
    sizes = S["sizes"]
    cols = {"Quickselect": "#d6336c", "Median of medians": "#4c6ef5", "Sort then index": "#8c8c8c"}
    fig, ax = plt.subplots(1, 2, figsize=(7.0, 2.2))
    for name, c in cols.items():
        ax[0].plot(sizes, [S["time_ms"][str(n)][name] for n in sizes], marker="o", ms=2.5,
                   lw=1.2, color=c, label=name)
    ax[0].set_title("(a) Time to find the median")
    ax[0].set_xlabel("List size n")
    ax[0].set_ylabel("Time (ms)")
    ax[0].legend(frameon=False, fontsize=6.5, loc="upper left")
    for name in ("Quickselect", "Median of medians"):
        ax[1].plot(sizes, S["work_per_n"][name], marker="o", ms=2.5, lw=1.2, color=cols[name], label=name)
    ax[1].set_ylim(0, 5)
    ax[1].set_title("(b) Elements scanned per input element")
    ax[1].set_xlabel("List size n")
    ax[1].set_ylabel("Work / n")
    ax[1].legend(frameon=False, fontsize=6.5, loc="lower right")
    for a in ax:
        kfmt(a)
    fig.tight_layout()
    fig.savefig("figures/fig_c_selection.png")
    plt.close(fig)


# -------------------------------------------------------------------- strings
def strings_fig():
    A = R["alphabet"]["data"]
    P = R["pattern_length"]
    W = R["worst_case"]["data"]
    fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.35))

    # (a) comparisons per text character for each alphabet
    texts = list(A)
    w = 0.16
    for k, a in enumerate(STR):
        ax[0].bar([i + (k - 2) * w for i in range(len(texts))],
                  [A[t][a]["cmp_per_char"] for t in texts], w, color=COL[a], label=LBL[a])
    ax[0].set_xticks(range(len(texts)))
    ax[0].set_xticklabels(["Binary\n(2)", "DNA\n(4)", "English\n(~90)", "ASCII\n(95)"], fontsize=6)
    ax[0].set_ylabel("Comparisons per text character")
    ax[0].set_title("(a) Alphabet size (m = 8)")

    # (b) comparisons per character against pattern length (English)
    for a in STR:
        ax[1].plot(P["lengths"], P["data"][a]["cmp_per_char"], marker="o", ms=2.2, lw=1.1, color=COL[a])
    ax[1].set_xscale("log", base=2)
    ax[1].set_xticks(P["lengths"])
    ax[1].set_xticklabels(P["lengths"])
    ax[1].set_xlabel("Pattern length m")
    ax[1].set_title("(b) Pattern length (English)")

    # (c) worst cases, log scale
    cases = ["a^n / a^(m-1)b", "a^n / a^m", "random DNA / random"]
    nice = ["aⁿ / aᵐ⁻¹b", "aⁿ / aᵐ", "random DNA"]
    floor = 0.05
    for k, a in enumerate(STR):
        xs = [i + (k - 2) * w for i in range(len(cases))]
        ax[2].bar(xs, [max(W[c][a], floor) for c in cases], w, color=COL[a])
        for x, c in zip(xs, cases):
            if W[c][a] < floor:
                ax[2].text(x, floor * 1.2, "~0", ha="center", fontsize=5)
    ax[2].set_yscale("log")
    ax[2].set_ylim(floor, 300)
    ax[2].set_xticks(range(len(cases)))
    ax[2].set_xticklabels(nice, fontsize=6.5)
    ax[2].set_title("(c) Worst cases (n = 20,000, m = 100)")

    h, l = ax[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=5, frameon=False, fontsize=7)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig("figures/fig_c_strings.png")
    plt.close(fig)


if __name__ == "__main__":
    selection_fig()
    strings_fig()
    print("wrote figures/fig_c_selection.png and figures/fig_c_strings.png")
