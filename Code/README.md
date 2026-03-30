# Timetable Generator — Search (Project 4, L3 formulation)

This folder implements the **university timetable** problem from the planning document as a state-space search: partial assignments of courses to **(room, timeslot)** with hard constraints (no room double-booking, no instructor clash, room capacity ≥ enrollment) and soft penalties (preferred slots, gaps, daily load imbalance).

## What is implemented

| Piece | Location |
|--------|-----------|
| **DFS** | `search_algorithms.py` → `depth_first_search` |
| **Uniform Cost Search (UCS)** | `search_algorithms.py` → `uniform_cost_search` |
| **Greedy Best-First** (uses **h₂**) | `search_algorithms.py` → `greedy_best_first` |
| **A\*** with **h₁** and **h₂** | `search_algorithms.py` → `a_star_search` (via `run_all`) |
| **Heuristic h₁** (remaining courses) | `heuristics.py` → `h1_remaining_courses` |
| **Heuristic h₂** (h₁ + relaxed preference lower bound) | `heuristics.py` → `h2_relaxed_penalty` |
| **Soft costs** | `penalties.py` |
| **Visualization** | `visualize.py` + `main.py` |

**Libraries:** `heapq` is used only for priority queues; **NumPy** is used for grid arrays in plots. **All four search procedures are handwritten** (not imported from an AI/search library).

**Path cost** matches the document: each assignment adds **1 + marginal soft penalty**, where marginal soft is the increase in total soft penalty (preferred / gaps / imbalance) when adding that assignment.

## Setup

Python **3.10+** recommended.

```bash
cd Code
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

Optional flags:

```bash
python main.py --instance small --max-expansions 500000 --out output
```

- **`--instance small`** (default): 5 courses, 3 rooms, 9 slots — fast for UCS, A*, and all plots.
- **`--instance eight`**: 8 courses, 4 rooms, 12 slots — DFS is quick; UCS/A\* often need a large `--max-expansions`.
- **`--instance medium`**: 16 courses — very hard; increase `--max-expansions` or expect timeouts.

Outputs under `output/` (or your `--out` path):

- `compare_expansions.png` — nodes expanded per method.
- `trace_<algorithm>.png` — depth and **g** vs expansion index (search process).
- `heuristic_<algorithm>.png` — **h** (and **f** where applicable) vs expansion.
- `timetable_<algorithm>.png` — final grid (timeslots × rooms) when a goal was found.

## Programmatic use

```python
from timetable_problem import build_demo_small
from search_algorithms import a_star_search, uniform_cost_search
from heuristics import h1_remaining_courses, h2_relaxed_penalty

p = build_demo_small()
r = a_star_search(p, h2_relaxed_penalty)
print(r.path_cost, r.nodes_expanded, r.goal_state)
```

## File layout

```
Code/
  timetable_problem.py   # Courses, rooms, state, successors, hard constraints
  penalties.py           # Soft penalty total and step costs
  heuristics.py          # h1, h2
  search_algorithms.py   # DFS, UCS, Greedy, A* + traces
  visualize.py           # Matplotlib figures
  main.py                # CLI runner
  requirements.txt
  README.md
```

## Notes for the report

- **DFS** is not cost-optimal; it returns the first complete valid schedule.
- **UCS** and **A\*** (with admissible **h**) are cost-optimal for this formulation; **Greedy** is not.
- **h₂ ≥ h₁** pointwise on this implementation (extra non-negative term **P(n)**), so A\* with **h₂** typically expands fewer nodes than with **h₁** on the same instance.
