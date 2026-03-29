"""
Heuristic 1: remaining courses (admissible for step cost >= 1).
Heuristic 2: h1 + P(n) where P lower-bounds unavoidable preference penalty under
relaxed room/capacity (only instructor conflicts kept), gaps/imbalance lower bound 0.
"""
from __future__ import annotations

from typing import Set

from timetable_problem import State, TimetableProblem

from penalties import PREFERRED_VIOLATION

_H1_CACHE: dict[tuple[int, State], float] = {}
_H2_CACHE: dict[tuple[int, State], float] = {}


def clear_heuristic_cache() -> None:
    _H1_CACHE.clear()
    _H2_CACHE.clear()


def h1_remaining_courses(problem: TimetableProblem, state: State) -> float:
    k = (id(problem), state)
    if k in _H1_CACHE:
        return _H1_CACHE[k]
    v = float(len(problem.courses) - len(state))
    _H1_CACHE[k] = v
    return v


def _occupied_times_by_instructor(problem: TimetableProblem, state: State) -> dict[int, Set[int]]:
    occ: dict[int, Set[int]] = {}
    for c_idx, _r, t in state:
        iid = problem.courses[c_idx].instructor_id
        occ.setdefault(iid, set()).add(t)
    return occ


def min_preference_penalty_relaxed(problem: TimetableProblem, state: State, course_idx: int) -> float:
    """
    Minimum extra preference penalty for assigning `course_idx`, ignoring room conflicts:
    pick a timeslot where instructor is not already teaching; minimize preferred violation.
    """
    c = problem.courses[course_idx]
    busy = _occupied_times_by_instructor(problem, state).get(c.instructor_id, set())
    best = float("inf")
    for t in range(problem.num_timeslots):
        if t in busy:
            continue
        pen = 0 if t in c.preferred_slots else PREFERRED_VIOLATION
        if pen < best:
            best = pen
    return 0.0 if best == float("inf") else float(best)


def p_relaxed_preference_sum(problem: TimetableProblem, state: State) -> float:
    assigned = {a[0] for a in state}
    total = 0.0
    for ci in range(len(problem.courses)):
        if ci in assigned:
            continue
        total += min_preference_penalty_relaxed(problem, state, ci)
    return total


def h2_relaxed_penalty(problem: TimetableProblem, state: State) -> float:
    k = (id(problem), state)
    if k in _H2_CACHE:
        return _H2_CACHE[k]
    v = h1_remaining_courses(problem, state) + p_relaxed_preference_sum(problem, state)
    _H2_CACHE[k] = v
    return v
