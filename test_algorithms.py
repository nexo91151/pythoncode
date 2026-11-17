"""Correctness tests.  Run:  python3 test_algorithms.py"""
import random
import unittest

from selection import (quickselect, median_of_medians_select, sort_select,
                       kth_largest, median, percentile, top_k)
from string_matching import ALGORITHMS


def reference_matches(text, pat):
    """Independent oracle based on str.find (handles overlaps)."""
    out, i = [], text.find(pat)
    while i != -1:
        out.append(i)
        i = text.find(pat, i + 1)
    return out


class SelectionTests(unittest.TestCase):
    def setUp(self):
        random.seed(7)

    def test_random_lists_with_duplicates(self):
        for _ in range(1500):
            a = [random.randint(0, 15) for _ in range(random.randint(1, 80))]
            k = random.randint(1, len(a))
            expected = sorted(a)[k - 1]
            self.assertEqual(quickselect(a, k), expected)
            self.assertEqual(median_of_medians_select(a, k), expected)
            self.assertEqual(sort_select(a, k), expected)

    def test_special_inputs(self):
        for a in ([5], [3, 3, 3, 3], list(range(100)), list(range(100, 0, -1))):
            for k in (1, len(a) // 2 + 1, len(a)):
                self.assertEqual(median_of_medians_select(a, k), sorted(a)[k - 1])
                self.assertEqual(quickselect(a, k), sorted(a)[k - 1])

    def test_input_not_modified(self):
        a = [9, 1, 8, 2, 7, 3]
        copy = list(a)
        quickselect(a, 3)
        median_of_medians_select(a, 3)
        self.assertEqual(a, copy)

    def test_kth_largest_median_percentile_topk(self):
        a = [random.randint(0, 1000) for _ in range(501)]
        s = sorted(a)
        self.assertEqual(kth_largest(a, 1), s[-1])
        self.assertEqual(kth_largest(a, 10), s[-10])
        self.assertEqual(median(a), s[250])
        rank = -(-len(a) * 95 // 100)                    # ceil(501 * 0.95) = 476
        self.assertEqual(percentile(a, 95), s[rank - 1])
        self.assertEqual(sorted(top_k(a, 7)), s[-7:])

    def test_invalid_k(self):
        for k in (0, 4, -1):
            with self.assertRaises(ValueError):
                quickselect([1, 2, 3], k)
            with self.assertRaises(ValueError):
                median_of_medians_select([1, 2, 3], k)


class StringMatchingTests(unittest.TestCase):
    def setUp(self):
        random.seed(11)

    def check(self, text, pat):
        expected = reference_matches(text, pat)
        for name, f in ALGORITHMS.items():
            self.assertEqual(f(text, pat), expected, f"{name}: {text!r} / {pat!r}")

    def test_random_small_alphabets(self):
        for alphabet in ("ab", "abc", "ACGT"):
            for _ in range(1500):
                t = "".join(random.choice(alphabet) for _ in range(random.randint(0, 50)))
                p = "".join(random.choice(alphabet) for _ in range(random.randint(1, 6)))
                self.check(t, p)

    def test_overlapping_and_periodic(self):
        self.check("aaaaaaaa", "aaa")
        self.check("abababababab", "abab")
        self.check("abcabcabcabc", "abcabc")
        self.check("aabaabaaa", "aabaa")

    def test_edge_cases(self):
        self.check("", "a")
        self.check("a", "a")
        self.check("a", "b")
        self.check("abc", "abcd")
        self.check("abc", "abc")
        self.check("hello world", "o w")
        self.check("hello world", "xyz")

    def test_text_drawn_from_pattern_substrings(self):
        for _ in range(500):
            p = "".join(random.choice("abc") for _ in range(random.randint(2, 8)))
            t = "".join(p[:random.randint(1, len(p))] for _ in range(random.randint(1, 12)))
            self.check(t, p)

    def test_comparison_counter(self):
        stats = {}
        ALGORITHMS["quick_search"]("abcabcabc", "cab", stats)
        self.assertGreater(stats["cmp"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
