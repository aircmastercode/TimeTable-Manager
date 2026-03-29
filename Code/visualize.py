"""
Visualization of search traces and resulting timetables (matplotlib).
"""
from __future__ import annotations

import os
from typing import Dict, List, Optional

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from search_algorithms import SearchResult, SearchStep
from timetable_problem import State, TimetableProblem


def state_to_grid(problem: TimetableProblem, state: State) -> np.ndarray:
    """Shape (num_timeslots, num_rooms): course index or -1 for empty."""
    grid = np.full((problem.num_timeslots, len(problem.rooms)), -1, dtype=np.int32)
    for c_idx, r_idx, t in state:
        grid[t, r_idx] = c_idx
    return grid


def plot_timetable(
    problem: TimetableProblem,
    state: State,
    title: str,
    out_path: Optional[str] = None,
) -> None:
    """Gantt-style grid: rows = timeslots, columns = rooms."""
    grid = state_to_grid(problem, state)
    fig, ax = plt.subplots(figsize=(10, 6))
    try:
        cmap = plt.colormaps.get_cmap("tab20").resampled(max(len(problem.courses), 1))
    except AttributeError:
        cmap = plt.cm.get_cmap("tab20", max(len(problem.courses), 1))
    display = np.ma.masked_where(grid < 0, grid)
    im = ax.imshow(display, aspect="auto", cmap=cmap, vmin=0, vmax=max(len(problem.courses) - 1, 0))

    days = problem.num_timeslots // problem.periods_per_day
    for d in range(1, days):
        y = d * problem.periods_per_day - 0.5
        ax.axhline(y, color="white", linewidth=2)

    ax.set_xticks(range(len(problem.rooms)))
    ax.set_xticklabels([r.name for r in problem.rooms], rotation=15, ha="right")
    ax.set_yticks(range(problem.num_timeslots))
    labels = []
    for t in range(problem.num_timeslots):
        day = t // problem.periods_per_day
        slot = t % problem.periods_per_day
        labels.append(f"D{day + 1} P{slot + 1}")
    ax.set_yticklabels(labels)
    ax.set_xlabel("Room")
    ax.set_ylabel("Timeslot")
    ax.set_title(title)

    for t in range(problem.num_timeslots):
        for r in range(len(problem.rooms)):
            cid = int(grid[t, r])
            if cid >= 0:
                ax.text(
                    r,
                    t,
                    problem.courses[cid].name,
                    ha="center",
                    va="center",
                    color="black",
                    fontsize=7,
                    fontweight="bold",
                )

    plt.colorbar(im, ax=ax, label="Course index", fraction=0.03, pad=0.04)
    plt.tight_layout()
    if out_path:
        fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_search_trace(steps: List[SearchStep], title: str, out_path: Optional[str] = None) -> None:
    """Depth and g over expansions (search process)."""
    if not steps:
        return
    exp = np.array([s.expansion for s in steps])
    depth = np.array([s.depth for s in steps])
    gvals = np.array([s.g for s in steps])
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(exp, depth, color="steelblue", linewidth=0.8)
    axes[0].set_ylabel("Depth (assigned courses)")
    axes[0].set_title(title + " — depth vs expansion")
    axes[0].grid(True, alpha=0.3)

    axes[1].plot(exp, gvals, color="darkorange", linewidth=0.8)
    axes[1].set_ylabel("g (path cost)")
    axes[1].set_xlabel("Expansion index")
    axes[1].grid(True, alpha=0.3)
    plt.tight_layout()
    if out_path:
        fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_heuristic_trace(steps: List[SearchStep], title: str, out_path: Optional[str] = None) -> None:
    """h and f over expansions when recorded."""
    if not steps or steps[0].h is None:
        return
    exp = np.array([s.expansion for s in steps])
    hvals = np.array([s.h or 0.0 for s in steps])
    fvals = np.array([s.f if s.f is not None else s.g for s in steps])
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(exp, hvals, label="h", color="seagreen", linewidth=0.9)
    ax.plot(exp, fvals, label="f (or g)", color="purple", linewidth=0.9, alpha=0.7)
    ax.set_xlabel("Expansion index")
    ax.set_ylabel("Value")
    ax.set_title(title + " — heuristic trace")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    if out_path:
        fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_algorithm_comparison(results: Dict[str, SearchResult], out_path: Optional[str] = None) -> None:
    names = list(results.keys())
    expanded = [results[k].nodes_expanded for k in names]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(names, expanded, color="slategray")
    ax.set_ylabel("Nodes expanded")
    ax.set_title("Search cost comparison")
    plt.xticks(rotation=25, ha="right")
    plt.tight_layout()
    if out_path:
        fig.savefig(out_path, dpi=150)
    plt.close(fig)


def ensure_out_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)
