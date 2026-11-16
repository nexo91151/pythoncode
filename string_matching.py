"""Exact string matching algorithms.

Every function has the signature  f(text, pat, stats=None)  and returns the
sorted list of ALL start indices (overlaps included) where `pat` occurs in
`text`.  If `stats` is a dict, character comparisons are counted in
stats["cmp"] and examined alignments in stats["windows"] (benchmark only).

Implemented
-----------
* brute_force   - try every alignment                    O((n-m+1)m)
* rabin_karp    - rolling hash, verify on a hash hit     expected O(n+m)
* kmp           - prefix function, never re-reads text   Theta(n+m)
* boyer_moore   - right-to-left, bad char + good suffix  O(n/m) best, O(nm) worst
* quick_search  - Sunday's look-ahead shift              O(n/(m+1)) best, O(nm) worst

Run `python3 string_matching.py` for a small self-checking demonstration.
"""


def _tick(stats, count=1):
    # Count character comparisons when a stats dict is supplied.
    if stats is not None:
        stats["cmp"] = stats.get("cmp", 0) + count


# --------------------------------------------------------------------------
# 1. Brute force
# --------------------------------------------------------------------------
def brute_force(text, pat, stats=None):
    """Compare the pattern with the text at every shift s = 0 .. n-m."""
    n, m = len(text), len(pat)
    out = []
    for s in range(n - m + 1):                   # every possible alignment
        j = 0
        while j < m:                             # compare left to right ...
            _tick(stats)
            if text[s + j] != pat[j]:            # ... stop at the first mismatch
                break
            j += 1
        if j == m:                               # all m characters matched
            out.append(s)
    return out


# --------------------------------------------------------------------------
# 2. Rabin-Karp
# --------------------------------------------------------------------------
def rabin_karp(text, pat, stats=None, d=256, q=1_000_000_007):
    """Compare rolling hashes first; verify characters only when hashes agree."""
    n, m = len(text), len(pat)
    if m > n:
        return []
    h = pow(d, m - 1, q)                         # weight of the leading character
    p = t = 0                                    # hash of pattern / current window
    for i in range(m):                           # hash the pattern and the first window
        p = (d * p + ord(pat[i])) % q
        t = (d * t + ord(text[i])) % q
    out = []
    for s in range(n - m + 1):
        if p == t:                               # hash hit: could be a spurious hit,
            j = 0                                # so verify the characters
            while j < m:
                _tick(stats)
                if text[s + j] != pat[j]:
                    break
                j += 1
            if j == m:
                out.append(s)
        if s < n - m:                            # roll the hash: drop text[s], add text[s+m]
            t = (d * (t - ord(text[s]) * h) + ord(text[s + m])) % q
    return out


# --------------------------------------------------------------------------
# 3. Knuth-Morris-Pratt
# --------------------------------------------------------------------------
def prefix_function(pat):
    """pi[i] = longest proper prefix of pat[:i+1] that is also its suffix (a border)."""
    # Example: prefix_function("ababaca") == [0, 0, 1, 2, 3, 0, 1]
    pi = [0] * len(pat)
    k = 0                                        # length of the current border
    for i in range(1, len(pat)):
        while k and pat[k] != pat[i]:            # mismatch: fall back to a shorter border
            k = pi[k - 1]
        if pat[k] == pat[i]:                     # match: the border grows by one
            k += 1
        pi[i] = k
    return pi


def kmp(text, pat, stats=None):
    """The text pointer never moves backwards; pi says how much to reuse."""
    n, m = len(text), len(pat)
    if m == 0:
        return list(range(n + 1))
    pi = prefix_function(pat)
    out, q = [], 0                               # q = characters of pat matched so far
    for i in range(n):
        while True:
            _tick(stats)
            if pat[q] == text[i]:                # next pattern character matches
                q += 1
                break
            if q == 0:                           # nothing to fall back to: move on
                break
            q = pi[q - 1]                        # mismatch: reuse the longest border
        if q == m:                               # full match ending at text[i]
            out.append(i - m + 1)
            q = pi[q - 1]                        # continue, allowing overlaps
    return out


# --------------------------------------------------------------------------
# 4. Boyer-Moore (bad-character + strong good-suffix rules)
# --------------------------------------------------------------------------
def _bad_char_table(pat):
    # Index of the LAST occurrence of every character in the pattern.
    return {c: i for i, c in enumerate(pat)}


def _good_suffix_table(pat):
    """shift[j] = how far to slide the pattern when the suffix pat[j:] has
    matched but the character before it has not (classical border-based
    preprocessing)."""
    m = len(pat)
    shift = [0] * (m + 1)
    border = [0] * (m + 1)
    i, j = m, m + 1
    border[i] = j
    while i > 0:                                 # case 1: the suffix re-occurs inside pat
        while j <= m and pat[i - 1] != pat[j - 1]:
            if shift[j] == 0:
                shift[j] = j - i
            j = border[j]
        i -= 1
        j -= 1
        border[i] = j
    j = border[0]
    for i in range(m + 1):                       # case 2: a prefix of pat matches a suffix
        if shift[i] == 0:
            shift[i] = j
        if i == j:
            j = border[j]
    return shift


def boyer_moore(text, pat, stats=None):
    """Compare right to left; on a mismatch shift by the larger of the two rules."""
    n, m = len(text), len(pat)
    if m == 0:
        return list(range(n + 1))
    last = _bad_char_table(pat)
    gs = _good_suffix_table(pat)
    out = []
    s = 0                                        # current shift of the pattern
    while s <= n - m:
        if stats is not None:                    # count examined alignments
            stats["windows"] = stats.get("windows", 0) + 1
        j = m - 1
        while j >= 0:                            # compare from the END of the pattern
            _tick(stats)
            if pat[j] != text[s + j]:
                break
            j -= 1
        if j < 0:                                # whole pattern matched
            out.append(s)
            s += gs[0]                           # slide to the next possible overlap
        else:                                    # mismatch at pattern index j:
            bad = j - last.get(text[s + j], -1)  #   bad-character shift
            s += max(gs[j + 1], bad)             #   take the larger safe shift
    return out


# --------------------------------------------------------------------------
# 5. Quick Search (Sunday, 1990)
# --------------------------------------------------------------------------
def quick_search_table(pat):
    """shift[c] = m - (right-most index of c in pat); absent characters use m + 1."""
    m = len(pat)
    return {c: m - i for i, c in enumerate(pat)}  # later (right-most) index wins


def quick_search(text, pat, stats=None):
    """After each window, shift using ONLY the text character just beyond it."""
    n, m = len(text), len(pat)
    if m == 0:
        return list(range(n + 1))
    table = quick_search_table(pat)
    out = []
    s = 0
    while s <= n - m:
        if stats is not None:                    # count examined alignments
            stats["windows"] = stats.get("windows", 0) + 1
        j = 0
        while j < m:                             # compare the window (any order works)
            _tick(stats)
            if pat[j] != text[s + j]:
                break
            j += 1
        if j == m:                               # match at shift s
            out.append(s)
        if s + m >= n:                           # no look-ahead character: finished
            break
        s += table.get(text[s + m], m + 1)       # look-ahead character decides the shift
    return out


ALGORITHMS = {
    "brute_force": brute_force,
    "rabin_karp": rabin_karp,
    "kmp": kmp,
    "boyer_moore": boyer_moore,
    "quick_search": quick_search,
}


# --------------------------------------------------------------------------
# Demonstration: python3 string_matching.py
# --------------------------------------------------------------------------
if __name__ == "__main__":
    text, pat = "HERE IS A SIMPLE EXAMPLE", "EXAMPLE"
    print(f"text    : {text!r}\npattern : {pat!r}")
    expected = [i for i in range(len(text) - len(pat) + 1) if text.startswith(pat, i)]
    for name, f in ALGORITHMS.items():
        stats = {}
        hits = f(text, pat, stats)
        assert hits == expected                  # every algorithm must agree
        print(f"{name:<13} match at {hits}   character comparisons: {stats.get('cmp', 0)}")
    print("prefix function of 'ababaca':", prefix_function("ababaca"))
    print("quick search table for 'EXAMPLE':", quick_search_table("EXAMPLE"))
    print("all string matching checks passed")
