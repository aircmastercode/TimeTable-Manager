# Timetable Generator — Search (Project 4, L3 formulation)

This folder implements the **university timetable** problem from the planning document as a state-space search: partial assignments of courses to **(room, timeslot)** with hard constraints (no room double-booking, no instructor clash, room capacity ≥ enrollment) and soft penalties (preferred slots, gaps, daily load imbalance).

## What is implemented

| Piece | Location |
|--------|-----------|
| **DFS** | `search_algorithms.py` → `depth_first_search` |
| **Uniform Cost Search (UCS)** | `search_algorithms.py` → `uniform_cost_search` |
| **Greedy Best-First** (uses **h₂**) | `search_algorithms.py` → `greedy_best_first` |
| **A\*** with **h₁** and **h₂** | `search_algorithms.py` → `a_star_search` (CLI: `--algo astar_h1` / `astar_h2`, or `--algo all`) |
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

From this folder (`Code/`), with the virtualenv activated:

```bash
python main.py
```

Defaults: `--instance small`, `--algo all`, `--max-expansions 500000`, `--out output`.

### Flags

| Flag | Values | Meaning |
|------|--------|--------|
| `--instance` | `small` (default), `eight`, `medium` | Problem size: 5 / 8 / 16 courses. |
| `--algo` | `all` (default), `dfs`, `ucs`, `greedy_h2`, `astar_h1`, `astar_h2` | Run every algorithm, or only one. |
| `--max-expansions` | integer (default `500000`) | Stop each search after this many **state expansions** (no goal ⇒ algorithm hit the cap or exhausted search). |
| `--out` | directory path (default `output`) | Where PNG figures are written. |

- **`--instance small`**: 5 courses, 3 rooms, 9 slots — good for running **`--algo all`**.
- **`--instance eight`**: 8 courses — DFS is often still fine; UCS / A* may need a **larger** `--max-expansions`.
- **`--instance medium`**: 16 courses — very hard; prefer **`--algo`** with a **single** algorithm and tune `--max-expansions`.

### Example commands

Run all algorithms on the small instance (writes `compare_expansions.png` plus per-algorithm plots):

```bash
python main.py --instance small --algo all --max-expansions 500000 --out output
```

Run only one algorithm (no `compare_expansions.png`; trace / heuristic / timetable still produced for that run):

```bash
python main.py --instance medium --algo ucs --max-expansions 500000 --out output_ucs
python main.py --instance medium --algo astar_h2 --max-expansions 500000 --out output_astar_h2
python main.py --instance eight --algo dfs --max-expansions 500000 --out output_dfs
python main.py --instance small --algo greedy_h2 --max-expansions 500000 --out output_greedy_h2
python main.py --instance small --algo astar_h1 --max-expansions 500000 --out output_astar_h1
```

Quick default (same as `python main.py`):

```bash
python main.py --instance small --algo all --out output
```

### Outputs (under `--out`)

- `compare_expansions.png` — only when **`--algo all`** (bar chart of nodes expanded per method).
- `trace_<name>.png` — depth and **g** vs expansion index (`<name>` matches `--algo` key, e.g. `dfs`, `ucs`, `greedy_h2`, `astar_h1`, `astar_h2`).
- `heuristic_<name>.png` — **h** (and **f** where applicable) vs expansion when traced.
- `timetable_<name>.png` — final grid (timeslots × rooms) when a goal was found.

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
