"""Selection algorithms: find the k-th smallest / largest element of a list.

Implemented
-----------
* sort_select                - sort, then index          O(n log n)   (baseline)
* quickselect                - random pivot              expected O(n)
* median_of_medians_select   - deterministic pivot       worst-case O(n)

Conventions: `a` is a list, `k` is a 1-indexed rank (k = 1 is the minimum).
The caller's list is never modified.  The optional `stats` dict counts the
elements scanned by partitioning (used only by benchmark.py).

Run `python3 selection.py` for a small self-checking demonstration.
"""
import random


def _check(a, k):
    # Reject ranks outside 1..n so every algorithm fails the same way.
    if not 1 <= k <= len(a):
        raise ValueError(f"k={k} out of range for a list of {len(a)} items")


# --------------------------------------------------------------------------
# Baseline: selection by sorting
# --------------------------------------------------------------------------
def sort_select(a, k):
    """Sort the whole list and index into it: O(n log n)."""
    _check(a, k)
    return sorted(a)[k - 1]


# --------------------------------------------------------------------------
# Quickselect: randomized selection, expected O(n)
# --------------------------------------------------------------------------
def quickselect(a, k, stats=None):
    """k-th smallest item using a random pivot and three-way partitioning."""
    _check(a, k)
    a = list(a)                                  # work on a copy
    while True:
        if stats is not None:                    # optional work counter
            stats["work"] = stats.get("work", 0) + len(a)
        pivot = random.choice(a)                 # 1. pick a random pivot
        lo = [x for x in a if x < pivot]         # 2. three-way partition:
        eq = [x for x in a if x == pivot]        #    < pivot, == pivot, > pivot
        if k <= len(lo):                         # 3. rank k lies among the smaller items
            a = lo
        elif k <= len(lo) + len(eq):             #    rank k is the pivot value itself
            return pivot
        else:                                    #    rank k lies among the larger items:
            k -= len(lo) + len(eq)               #    re-number k inside that part
            a = [x for x in a if x > pivot]


# --------------------------------------------------------------------------
# Median of medians: deterministic selection, worst-case O(n)
# --------------------------------------------------------------------------
def median_of_medians_select(a, k, stats=None):
    """k-th smallest item in worst-case O(n) time (Blum et al., 1973).

    The pivot is the median of the medians of groups of five.  At least
    ~30% of the items are <= pivot and ~30% are >= pivot, so the recursive
    call below never sees more than ~70% of the list:
        T(n) <= T(n/5) + T(7n/10) + O(n)  =>  T(n) = O(n)
    """
    _check(a, k)
    return _mom(list(a), k, stats)


def _mom(a, k, stats=None):
    if stats is not None:                        # optional work counter
        stats["work"] = stats.get("work", 0) + len(a)
    if len(a) <= 5:                              # base case: sort the tiny list
        return sorted(a)[k - 1]
    # 1. cut the list into groups of five and sort each group (constant time each)
    groups = [sorted(a[i:i + 5]) for i in range(0, len(a), 5)]
    # 2. the median of every group (the last group may hold fewer than five items)
    medians = [g[len(g) // 2] for g in groups]
    # 3. recursively select the median of those medians: this is the pivot
    pivot = _mom(medians, (len(medians) + 1) // 2, stats)
    # 4. partition around the pivot (three-way, so duplicates are handled)
    lo = [x for x in a if x < pivot]
    eq = [x for x in a if x == pivot]
    # 5. recurse into the one part that contains rank k
    if k <= len(lo):
        return _mom(lo, k, stats)
    if k <= len(lo) + len(eq):
        return pivot
    hi = [x for x in a if x > pivot]
    return _mom(hi, k - len(lo) - len(eq), stats)


# --------------------------------------------------------------------------
# Convenience wrappers (each needs one selection call, so each is O(n))
# --------------------------------------------------------------------------
def kth_largest(a, k, select=median_of_medians_select):
    """k-th largest item (k = 1 is the maximum)."""
    _check(a, k)
    return select(a, len(a) - k + 1)             # k-th largest = (n-k+1)-th smallest


def median(a, select=median_of_medians_select):
    """Lower median."""
    return select(a, (len(a) + 1) // 2)


def percentile(a, p, select=median_of_medians_select):
    """Nearest-rank percentile, 0 < p <= 100."""
    if not 0 < p <= 100:
        raise ValueError("p must be in (0, 100]")
    rank = max(1, -(-len(a) * p // 100))         # ceil(n * p / 100)
    return select(a, int(rank))


def top_k(a, k, select=quickselect):
    """The k largest items (unordered) with one selection call plus one pass."""
    _check(a, k)
    threshold = kth_largest(a, k, select)        # k-th largest value
    out = [x for x in a if x > threshold]        # everything strictly above it
    out += [threshold] * (k - len(out))          # fill the remaining slots with ties
    return out


# --------------------------------------------------------------------------
# Demonstration: python3 selection.py
# --------------------------------------------------------------------------
if __name__ == "__main__":
    data = [12, 3, 17, 8, 25, 1, 14, 9, 30, 6, 21, 4, 19, 11, 27]
    print("list              :", data)
    print("sorted (reference):", sorted(data))
    for k in (1, 5, 8, 15):
        q, m, s = quickselect(data, k), median_of_medians_select(data, k), sort_select(data, k)
        assert q == m == s                       # all three must agree
        print(f"k={k:<2} smallest -> quickselect={q:<3} median-of-medians={m:<3} sort={s}")
    print("3rd largest       :", kth_largest(data, 3))
    print("median            :", median(data))
    print("95th percentile   :", percentile(data, 95))
    print("top-3 (unordered) :", sorted(top_k(data, 3)))
    print("all selection checks passed")
