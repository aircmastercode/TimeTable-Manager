"""
Soft constraint penalties (planning doc): preferred slots, gaps, daily imbalance.
g(state) accumulates: each step adds 1 + marginal_soft.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Tuple

from timetable_problem import State, TimetableProblem

PREFERRED_VIOLATION = 5
GAP_UNIT = 5
IMBALANCE_UNIT = 10

_SOFT_CACHE: dict[tuple[int, State], int] = {}


def clear_penalty_cache() -> None:
    _SOFT_CACHE.clear()


def _instructor_slots(problem: TimetableProblem, state: State) -> Dict[int, Dict[int, List[int]]]:
    """instructor_id -> day -> sorted list of timeslot indices."""
    by_inst_day: Dict[int, Dict[int, List[int]]] = defaultdict(lambda: defaultdict(list))
    for c_idx, _r, t in state:
        inst = problem.courses[c_idx].instructor_id
        d = problem.slot_day(t)
        by_inst_day[inst][d].append(t)
    for inst in by_inst_day:
        for d in by_inst_day[inst]:
            by_inst_day[inst][d].sort()
    return by_inst_day


def soft_penalty_total(problem: TimetableProblem, state: State) -> int:
    """
    Total soft penalty for a partial schedule (non-negative).
    - Preferred: +5 per assignment outside instructor preferred set.
    - Gaps: +5 per empty slot between two classes same instructor same day.
    - Imbalance: +10 * max(0, max_day_load - min_day_load - 1) per instructor.
    """
    key = (id(problem), state)
    hit = _SOFT_CACHE.get(key)
    if hit is not None:
        return hit
    if not state:
        _SOFT_CACHE[key] = 0
        return 0
    pref_cost = 0
    for c_idx, _r, t in state:
        c = problem.courses[c_idx]
        if t not in c.preferred_slots:
            pref_cost += PREFERRED_VIOLATION

    gap_cost = 0
    by_inst_day = _instructor_slots(problem, state)
    for _inst, days in by_inst_day.items():
        for _day, slots in days.items():
            if len(slots) < 2:
                continue
            for i in range(len(slots) - 1):
                gap = slots[i + 1] - slots[i] - 1
                if gap > 0:
                    gap_cost += GAP_UNIT * gap

    imb_cost = 0
    num_days = (problem.num_timeslots + problem.periods_per_day - 1) // problem.periods_per_day
    for _inst, days in by_inst_day.items():
        loads = [len(days.get(d, [])) for d in range(num_days)]
        if not any(loads):
            continue
        mx = max(loads)
        mn = min(loads)
        diff = mx - mn
        if diff > 1:
            imb_cost += IMBALANCE_UNIT * (diff - 1)

    total = pref_cost + gap_cost + imb_cost
    _SOFT_CACHE[key] = total
    return total


def step_cost(
    problem: TimetableProblem, parent: State, child: State
) -> int:
    """Cost of transition parent -> child: 1 + (soft(child)-soft(parent))."""
    return 1 + soft_penalty_total(problem, child) - soft_penalty_total(problem, parent)


def path_cost_g(problem: TimetableProblem, state: State) -> int:
    """Path cost from empty state: |assignments| + soft_total (matches doc's g with additive soft)."""
    return len(state) + soft_penalty_total(problem, state)
