"""Log Analyzer - an application of string matching and selection algorithms.

Scenario: a web server writes one line per request, e.g.

    2026-10-01 12:00:01 ERROR 10.0.3.7 GET /api/orders 500 1840ms

The tool answers two everyday questions about a (possibly very large) log:

  search  Which lines contain a given pattern (e.g. "ERROR" or "/api/orders")?
          -> uses one of the string matching algorithms.
  stats   For the lines that match, what are the median / 95th / 99th
          percentile response time and the k slowest requests?
          -> uses the selection algorithms (O(n), no full sort needed).

Usage examples
--------------
  python3 log_analyzer.py generate sample.log --lines 100000
  python3 log_analyzer.py search sample.log "ERROR" --algo quick_search --show 5
  python3 log_analyzer.py stats  sample.log "/api/orders" --top 5
  python3 log_analyzer.py compare sample.log "POST /api/orders 50"
"""
import argparse
import bisect
import random
import re
import sys
import time

import selection
from string_matching import ALGORITHMS

LATENCY = re.compile(r"(\d+)ms\s*$")
LEVELS = [("INFO", 0.85), ("WARN", 0.10), ("ERROR", 0.05)]
ENDPOINTS = ["/api/users", "/api/orders", "/api/products", "/api/cart",
             "/api/login", "/api/search", "/health", "/static/app.js"]
METHODS = ["GET", "GET", "GET", "POST", "PUT", "DELETE"]


# --------------------------------------------------------------------------
# Sample data
# --------------------------------------------------------------------------
def generate_log(path, lines=100_000, seed=42):
    """Write a reproducible synthetic access log."""
    rnd = random.Random(seed)
    t = 0
    with open(path, "w") as f:
        for _ in range(lines):
            t += rnd.randint(0, 2)
            h, rem = divmod(t % 86400, 3600)
            mi, sec = divmod(rem, 60)
            level = rnd.choices([l for l, _ in LEVELS], [w for _, w in LEVELS])[0]
            status = {"INFO": 200, "WARN": rnd.choice([301, 404, 429]),
                      "ERROR": rnd.choice([500, 502, 503])}[level]
            base = rnd.lognormvariate(4.4, 0.6)             # ~80 ms typical
            ms = int(base * (6 if level == "ERROR" else 1))
            ip = f"10.0.{rnd.randint(0, 9)}.{rnd.randint(1, 254)}"
            f.write(f"2026-10-01 {h:02d}:{mi:02d}:{sec:02d} {level} {ip} "
                    f"{rnd.choice(METHODS)} {rnd.choice(ENDPOINTS)} {status} {ms}ms\n")


# --------------------------------------------------------------------------
# Core: search a whole log with a string matching algorithm
# --------------------------------------------------------------------------
def newline_offsets(text):
    """Offsets of every '\\n' (uses the C-level str.find, one call per line)."""
    out, i = [], text.find("\n")
    while i != -1:
        out.append(i)
        i = text.find("\n", i + 1)
    return out


def find_matching_lines(text, pattern, algo="quick_search"):
    """Return the sorted line numbers (0-based) of lines containing `pattern`.

    The matcher runs once over the entire text; every hit is mapped to its
    line with a binary search over the newline offsets.  A pattern is not
    allowed to contain a newline, so a hit never spans two lines.
    """
    if "\n" in pattern or not pattern:
        raise ValueError("pattern must be non-empty and contain no newline")
    matcher = ALGORITHMS[algo]
    newlines = newline_offsets(text)
    hits = matcher(text, pattern)
    lines = sorted({bisect.bisect_left(newlines, pos) for pos in hits})
    return lines, newlines


def line_text(text, newlines, line_no):
    start = 0 if line_no == 0 else newlines[line_no - 1] + 1
    end = newlines[line_no] if line_no < len(newlines) else len(text)
    return text[start:end]


def latencies(text, newlines, line_numbers):
    out = []
    for n in line_numbers:
        m = LATENCY.search(line_text(text, newlines, n))
        if m:
            out.append(int(m.group(1)))
    return out


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------
def read(path):
    with open(path) as f:
        return f.read()


def cmd_search(args):
    text = read(args.file)
    t0 = time.perf_counter()
    lines, newlines = find_matching_lines(text, args.pattern, args.algo)
    dt = time.perf_counter() - t0
    print(f"[{args.algo}] {len(lines)} matching lines of {len(newlines)} "
          f"in {dt * 1000:.1f} ms")
    for n in lines[:args.show]:
        print(f"  {n + 1:>7}: {line_text(text, newlines, n)}")


def cmd_stats(args):
    text = read(args.file)
    lines, newlines = find_matching_lines(text, args.pattern, args.algo)
    lat = latencies(text, newlines, lines)
    if not lat:
        print("no matching lines with a latency value")
        return
    sel = selection.median_of_medians_select
    print(f"pattern {args.pattern!r}: {len(lat)} requests")
    print(f"  median : {selection.median(lat, sel)} ms")
    print(f"  p95    : {selection.percentile(lat, 95, sel)} ms")
    print(f"  p99    : {selection.percentile(lat, 99, sel)} ms")
    print(f"  slowest: {selection.kth_largest(lat, 1, sel)} ms")
    k = min(args.top, len(lat))
    print(f"  {k} slowest requests (via top-k selection):")
    slow = set(selection.top_k(lat, k))
    shown = 0
    for n in lines:
        row = line_text(text, newlines, n)
        m = LATENCY.search(row)
        if m and int(m.group(1)) in slow and shown < k:
            print(f"    {row}")
            shown += 1


def cmd_compare(args):
    text = read(args.file)
    print(f"pattern {args.pattern!r} in {len(text):,} characters")
    reference = None
    for name, f in ALGORITHMS.items():
        t0 = time.perf_counter()
        hits = f(text, args.pattern)
        dt = time.perf_counter() - t0
        reference = hits if reference is None else reference
        assert hits == reference, f"{name} disagrees with the others"
        print(f"  {name:<13} {len(hits):>7} hits  {dt * 1000:8.1f} ms")


def cmd_demo():
    """`python3 log_analyzer.py` with no arguments: generate a log, then run
    a search, a statistics report and an algorithm comparison on it."""
    path = "sample.log"
    generate_log(path, 100_000)
    print(f"generated {path} (100,000 lines)\n")
    ns = argparse.Namespace
    cmd_search(ns(file=path, pattern="POST /api/orders 50", algo="quick_search", show=3))
    print()
    cmd_stats(ns(file=path, pattern="ERROR", algo="quick_search", top=3))
    print()
    cmd_compare(ns(file=path, pattern="POST /api/orders 50"))


def main(argv=None):
    if argv is None and len(sys.argv) == 1:       # no arguments: run the demo
        return cmd_demo()
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="write a synthetic log file")
    g.add_argument("file")
    g.add_argument("--lines", type=int, default=100_000)

    for name in ("search", "stats", "compare"):
        s = sub.add_parser(name)
        s.add_argument("file")
        s.add_argument("pattern")
        if name != "compare":
            s.add_argument("--algo", choices=ALGORITHMS, default="quick_search")
        if name == "search":
            s.add_argument("--show", type=int, default=5)
        if name == "stats":
            s.add_argument("--top", type=int, default=5)

    args = p.parse_args(argv)
    if args.cmd == "generate":
        generate_log(args.file, args.lines)
        print(f"wrote {args.lines} lines to {args.file}")
    else:
        {"search": cmd_search, "stats": cmd_stats, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
