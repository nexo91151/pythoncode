# Selection and String Matching Algorithms

Python 3 code for the report `Selection_and_String_Matching_Report_Short.docx`
(textbook: Agarwal, 2022, Chapters 12-13). Standard library only, except where noted.

## Executable files

| File | Command | What you see |
|---|---|---|
| `selection.py` | `python3 selection.py` | quickselect, median of medians and sorting agree for k = 1, 5, 8, 15; k-th largest, median, percentile, top-k |
| `string_matching.py` | `python3 string_matching.py` | all five matchers find `EXAMPLE` at shift 17; comparison counts 27, 7, 27, 15, 10 |
| `test_algorithms.py` | `python3 test_algorithms.py` | 10 unit tests against independent oracles; ends with `OK` |
| `log_analyzer.py` | `python3 log_analyzer.py` | application demo (generates `sample.log`, then search, stats, compare) |
| `log_analyzer.py` | `python3 log_analyzer.py search sample.log "ERROR" --algo kmp` | also: `generate`, `stats`, `compare` |
| `benchmark.py` | `python3 benchmark.py` | all experiments (~2 min); writes `results.json` and `figures/` (needs matplotlib) |
| `make_compact_figs.py` | `python3 make_compact_figs.py` | redraws report Figures 1 and 3 from `results.json` (needs matplotlib) |
| `make_figures.py` | `python3 make_figures.py` | redraws report Figure 2, the Quick Search trace (needs matplotlib) |

`selection.py` and `string_matching.py` can also be imported as libraries.

## Interfaces

* Selection: `f(a, k)` returns the k-th smallest item (1-indexed); the list is not
  modified; `ValueError` for an invalid `k`.
* String matching: `f(text, pat, stats=None)` returns every start index of `pat` in
  `text` (overlaps included). Pass `stats={}` to count character comparisons
  (`stats["cmp"]`) and examined alignments (`stats["windows"]`).

Operation counts are reproducible; wall-clock times depend on the machine.
