"""Diagrams for the report: Quick Search trace and application architecture.
Run:  python3 make_figures.py   (writes figures/fig_qs_trace.png, fig_architecture.png)
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle

from string_matching import quick_search_table

plt.rcParams.update({"font.family": "DejaVu Sans Mono", "figure.dpi": 200})
PINK, GREEN, RED, GREY, BLUE = "#d6336c", "#2f9e44", "#e03131", "#dee2e6", "#4c6ef5"


def qs_trace(text="HERE IS A SIMPLE EXAMPLE", pat="EXAMPLE"):
    n, m = len(text), len(pat)
    table = quick_search_table(pat)
    windows, s = [], 0
    while s <= n - m:
        j = 0
        while j < m and pat[j] == text[s + j]:
            j += 1
        nxt = text[s + m] if s + m < n else None
        shift = table.get(nxt, m + 1) if nxt is not None else None
        windows.append((s, j, nxt, shift))
        if s + m >= n:
            break
        s += shift
    return windows


def draw_trace():
    text, pat = "HERE IS A SIMPLE EXAMPLE", "EXAMPLE"
    n, m = len(text), len(pat)
    wins = qs_trace(text, pat)
    rows = len(wins) + 1
    fig, ax = plt.subplots(figsize=(7.4, 0.4 * rows + 0.5))
    ax.set_xlim(-3.2, n + 11.5)
    ax.set_ylim(-len(wins) - 0.3, 1.4)
    ax.axis("off")

    def cell(x, y, ch, face, edge="white", color="black"):
        ax.add_patch(Rectangle((x, y), 0.94, 0.8, facecolor=face, edgecolor=edge, lw=0.6))
        ax.text(x + 0.47, y + 0.4, "·" if ch == " " else ch, ha="center", va="center",
                fontsize=7.5, color=color)

    ax.text(-3.0, 0.4, "text", fontsize=7.5, va="center", fontweight="bold")
    for i, ch in enumerate(text):
        cell(i, 0, ch, "#f1f3f5", edge="#adb5bd")
        ax.text(i + 0.47, 1.05, str(i), ha="center", fontsize=5, color="#868e96")

    for r, (s, j, nxt, shift) in enumerate(wins, start=1):
        y = -r
        ax.text(-3.0, y + 0.4, f"s={s}", fontsize=7.5, va="center")
        matched = j == m
        for k in range(m):
            if matched or k < j:
                face, col = GREEN, "white"
            elif k == j:
                face, col = RED, "white"
            else:
                face, col = GREY, "black"
            cell(s + k, y, pat[k], face, color=col)
        if nxt is not None:
            cell(s + m, y, nxt, PINK, color="white")
            note = f"next char '{'·' if nxt == ' ' else nxt}' -> shift {shift}"
        else:
            note = "match; end of text"
        ax.text(n + 0.8, y + 0.4, note, fontsize=7, va="center")

    ax.text(-3.0, -len(wins) - 0.25,
            "green = matched   red = first mismatch   grey = not compared   "
            "pink = look-ahead character text[s+m]   (· = space)",
            fontsize=6.2, color="#495057", va="top")
    fig.savefig("figures/fig_qs_trace.png", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def draw_architecture():
    fig, ax = plt.subplots(figsize=(7.4, 3.3))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 46)
    ax.axis("off")
    plt.rcParams["font.family"] = "DejaVu Sans"

    def box(x, y, w, h, title, sub, face, edge):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.6",
                                    facecolor=face, edgecolor=edge, lw=1.1))
        ax.text(x + w / 2, y + h * 0.64, title, ha="center", va="center", fontsize=7.6,
                fontweight="bold", family="DejaVu Sans")
        ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center", fontsize=6.2,
                color="#343a40", family="DejaVu Sans")

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=9,
                                     color="#495057", lw=1.1))

    sm_face, sm_edge = "#ffe3ec", PINK
    se_face, se_edge = "#e3e9ff", BLUE
    nt_face, nt_edge = "#f1f3f5", "#868e96"

    # row 1: string matching
    box(1, 28, 20, 14, "Log file", "100,000 lines\n(one big string)", nt_face, nt_edge)
    box(28, 28, 22, 14, "String matcher", "Quick Search / Boyer-Moore\nKMP / Rabin-Karp / brute force", sm_face, sm_edge)
    box(57, 28, 18, 14, "Hit offsets", "positions of the\npattern in the text", nt_face, nt_edge)
    box(81, 28, 18, 14, "Line index", "binary search over\nnewline offsets", nt_face, nt_edge)
    arrow(21.6, 35, 27.4, 35)
    arrow(50.6, 35, 56.4, 35)
    arrow(75.6, 35, 80.4, 35)

    # row 2: selection
    box(81, 4, 18, 14, "Latencies", "parse 'NNNms'\nfrom matching lines", nt_face, nt_edge)
    box(48, 4, 26, 14, "Selection", "median of medians\n/ quickselect (k-th element)", se_face, se_edge)
    box(1, 4, 40, 14, "Report", "median, p95, p99, slowest request,\ntop-k slowest lines", nt_face, nt_edge)
    arrow(90, 27.4, 90, 18.6)
    arrow(80.4, 11, 74.6, 11)
    arrow(47.4, 11, 41.6, 11)

    ax.text(1, 45.2, "String matching stage", fontsize=7, color=PINK, fontweight="bold")
    ax.text(1, 21.2, "Selection stage", fontsize=7, color=BLUE, fontweight="bold")
    fig.savefig("figures/fig_architecture.png", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


if __name__ == "__main__":
    draw_trace()
    draw_architecture()
    print("wrote figures/fig_qs_trace.png and figures/fig_architecture.png")
