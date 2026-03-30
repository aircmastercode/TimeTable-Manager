"""
Four search algorithms (own implementations). heapq only for priority queues.
DFS, UCS, Greedy Best-First, A*.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from heuristics import (
    clear_heuristic_cache,
    h1_remaining_courses,
    h2_relaxed_penalty,
)
from penalties import clear_penalty_cache, step_cost
from timetable_problem import State, TimetableProblem

HeuristicFn = Callable[[TimetableProblem, State], float]


@dataclass
class SearchStep:
    expansion: int
    algorithm: str
    depth: int
    g: float
    h: Optional[float]
    f: Optional[float]
    num_successors: int


@dataclass
class SearchResult:
    goal_state: Optional[State]
    path_cost: Optional[float]
    steps: List[SearchStep] = field(default_factory=list)
    nodes_expanded: int = 0
    max_frontier: int = 0


def _record_step(
    steps: List[SearchStep],
    algo: str,
    exp: int,
    state: State,
    g: float,
    h_fn: Optional[HeuristicFn],
    problem: TimetableProblem,
    num_succ: int,
    max_trace: int,
) -> None:
    if len(steps) >= max_trace:
        return
    h_val = h_fn(problem, state) if h_fn else None
    f_val = (g + h_val) if h_val is not None else None
    steps.append(
        SearchStep(
            expansion=exp,
            algorithm=algo,
            depth=len(state),
            g=g,
            h=h_val,
            f=f_val,
            num_successors=num_succ,
        )
    )


def depth_first_search(
    problem: TimetableProblem,
    max_expansions: int = 500_000,
    max_trace_steps: int = 5_000,
    h_trace: Optional[HeuristicFn] = None,
) -> SearchResult:
    """Depth-first: stack of (state, g). First goal found."""
    steps: List[SearchStep] = []
    stack: List[Tuple[State, float]] = [(frozenset(), 0.0)]
    expanded = 0
    max_frontier = 1

    while stack:
        state, g = stack.pop()
        expanded += 1
        succs = problem.successors(state)
        _record_step(steps, "DFS", expanded, state, g, h_trace, problem, len(succs), max_trace_steps)

        if expanded > max_expansions:
            return SearchResult(None, None, steps, expanded, max_frontier)

        if problem.is_goal(state):
            return SearchResult(state, g, steps, expanded, max_frontier)

        max_frontier = max(max_frontier, len(stack) + len(succs))
        for _c, _r, _t, child in reversed(succs):
            gc = g + step_cost(problem, state, child)
            stack.append((child, gc))

    return SearchResult(None, None, steps, expanded, max_frontier)


def uniform_cost_search(
    problem: TimetableProblem,
    max_expansions: int = 500_000,
    max_trace_steps: int = 5_000,
    h_trace: Optional[HeuristicFn] = None,
) -> SearchResult:
    """UCS: expand minimum g; graph search."""
    steps: List[SearchStep] = []
    tie = 0
    heap: List[Tuple[float, int, State]] = [(0.0, tie, frozenset())]
    best_g: Dict[State, float] = {frozenset(): 0.0}
    closed: set[State] = set()
    expanded = 0
    max_frontier = 1

    while heap:
        g, _, state = heapq.heappop(heap)
        if state in closed:
            continue
        if g > best_g.get(state, float("inf")) + 1e-9:
            continue
        closed.add(state)
        expanded += 1
        succs = problem.successors(state)
        _record_step(steps, "UCS", expanded, state, g, h_trace, problem, len(succs), max_trace_steps)

        if expanded > max_expansions:
            return SearchResult(None, None, steps, expanded, max_frontier)

        if problem.is_goal(state):
            return SearchResult(state, g, steps, expanded, max_frontier)

        for _c, _r, _t, child in succs:
            ng = g + step_cost(problem, state, child)
            if ng < best_g.get(child, float("inf")) - 1e-9:
                best_g[child] = ng
                tie += 1
                heapq.heappush(heap, (ng, tie, child))
        max_frontier = max(max_frontier, len(heap))

    return SearchResult(None, None, steps, expanded, max_frontier)


def greedy_best_first(
    problem: TimetableProblem,
    h_fn: HeuristicFn,
    max_expansions: int = 500_000,
    max_trace_steps: int = 5_000,
) -> SearchResult:
    """
    Greedy best-first: priority by h(n) only; tie-break by g.
    Stale entries dropped via best_g (same state may be reached with lower g later).
    """
    steps: List[SearchStep] = []
    tie = 0
    start = frozenset()
    h0 = h_fn(problem, start)
    heap: List[Tuple[float, int, float, State]] = [(h0, tie, 0.0, start)]
    best_g: Dict[State, float] = {start: 0.0}
    expanded = 0
    max_frontier = 1

    while heap:
        h_val, _, g, state = heapq.heappop(heap)
        if g > best_g.get(state, float("inf")) + 1e-9:
            continue
        expanded += 1
        succs = problem.successors(state)
        _record_step(steps, "Greedy", expanded, state, g, h_fn, problem, len(succs), max_trace_steps)

        if expanded > max_expansions:
            return SearchResult(None, None, steps, expanded, max_frontier)

        if problem.is_goal(state):
            return SearchResult(state, g, steps, expanded, max_frontier)

        for _c, _r, _t, child in succs:
            ng = g + step_cost(problem, state, child)
            if ng >= best_g.get(child, float("inf")) - 1e-9:
                continue
            best_g[child] = ng
            nh = h_fn(problem, child)
            tie += 1
            heapq.heappush(heap, (nh, tie, ng, child))
        max_frontier = max(max_frontier, len(heap))

    return SearchResult(None, None, steps, expanded, max_frontier)


def a_star_search(
    problem: TimetableProblem,
    h_fn: HeuristicFn,
    max_expansions: int = 500_000,
    max_trace_steps: int = 5_000,
) -> SearchResult:
    """
    A*: f = g + h with closed set and reopening when a strictly better g is found
    (needed if the heuristic is not consistent with the step-cost model).
    """
    steps: List[SearchStep] = []
    tie = 0
    start = frozenset()
    g_start = 0.0
    f_start = g_start + h_fn(problem, start)
    heap: List[Tuple[float, int, float, State]] = [(f_start, tie, g_start, start)]
    g_score: Dict[State, float] = {start: 0.0}
    closed: set[State] = set()
    expanded = 0
    max_frontier = 1

    while heap:
        _f_val, _, g, state = heapq.heappop(heap)
        if g > g_score.get(state, float("inf")) + 1e-9:
            continue
        if state in closed:
            continue
        closed.add(state)
        expanded += 1
        succs = problem.successors(state)
        _record_step(steps, "A*", expanded, state, g, h_fn, problem, len(succs), max_trace_steps)

        if expanded > max_expansions:
            return SearchResult(None, None, steps, expanded, max_frontier)

        if problem.is_goal(state):
            return SearchResult(state, g, steps, expanded, max_frontier)

        for _c, _r, _t, child in succs:
            ng = g + step_cost(problem, state, child)
            if ng < g_score.get(child, float("inf")) - 1e-9:
                g_score[child] = ng
                if child in closed:
                    closed.remove(child)
                nh = h_fn(problem, child)
                tie += 1
                heapq.heappush(heap, (ng + nh, tie, ng, child))
        max_frontier = max(max_frontier, len(heap))

    return SearchResult(None, None, steps, expanded, max_frontier)


def run_all(
    problem: TimetableProblem,
    max_expansions: int = 500_000,
    max_trace_steps: int = 5_000,
) -> Dict[str, SearchResult]:
    """Run DFS, UCS, Greedy(h2), A*(h1), A*(h2) for comparison."""
    clear_penalty_cache()
    clear_heuristic_cache()
    return {
        "dfs": depth_first_search(
            problem, max_expansions, max_trace_steps, h_trace=h2_relaxed_penalty
        ),
        "ucs": uniform_cost_search(
            problem, max_expansions, max_trace_steps, h_trace=h2_relaxed_penalty
        ),
        "greedy_h2": greedy_best_first(
            problem, h2_relaxed_penalty, max_expansions, max_trace_steps
        ),
        "astar_h1": a_star_search(
            problem, h1_remaining_courses, max_expansions, max_trace_steps
        ),
        "astar_h2": a_star_search(
            problem, h2_relaxed_penalty, max_expansions, max_trace_steps
        ),
    }


def run_selected(
    problem: TimetableProblem,
    algorithm: str,
    max_expansions: int = 500_000,
    max_trace_steps: int = 5_000,
) -> Dict[str, SearchResult]:
    """Run one selected algorithm or all (same keys as run_all)."""
    if algorithm == "all":
        return run_all(problem, max_expansions=max_expansions, max_trace_steps=max_trace_steps)

    clear_penalty_cache()
    clear_heuristic_cache()

    if algorithm == "dfs":
        return {
            "dfs": depth_first_search(
                problem, max_expansions, max_trace_steps, h_trace=h2_relaxed_penalty
            )
        }
    if algorithm == "ucs":
        return {
            "ucs": uniform_cost_search(
                problem, max_expansions, max_trace_steps, h_trace=h2_relaxed_penalty
            )
        }
    if algorithm == "greedy_h2":
        return {
            "greedy_h2": greedy_best_first(
                problem, h2_relaxed_penalty, max_expansions, max_trace_steps
            )
        }
    if algorithm == "astar_h1":
        return {
            "astar_h1": a_star_search(
                problem, h1_remaining_courses, max_expansions, max_trace_steps
            )
        }
    if algorithm == "astar_h2":
        return {
            "astar_h2": a_star_search(
                problem, h2_relaxed_penalty, max_expansions, max_trace_steps
            )
        }
    raise ValueError(f"Unknown algorithm: {algorithm}")
