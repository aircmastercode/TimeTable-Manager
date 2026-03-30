#!/usr/bin/env python3
"""
Timetable generator: run four search algorithms, both A* heuristics, save plots.
"""
from __future__ import annotations

import argparse
import os
import sys

from timetable_problem import build_demo_eight, build_demo_medium, build_demo_small
from search_algorithms import run_all
from visualize import (
    ensure_out_dir,
    plot_algorithm_comparison,
    plot_heuristic_trace,
    plot_search_trace,
    plot_timetable,
)


def main() -> int:
    p = argparse.ArgumentParser(description="Timetable search (DFS, UCS, Greedy, A*)")
    p.add_argument(
        "--instance",
        choices=("small", "eight", "medium"),
        default="small",
        help="small=5 courses (default); eight=8 courses; medium=16 courses.",
    )
    p.add_argument("--max-expansions", type=int, default=500_000)
    p.add_argument("--out", default="output", help="Directory for PNG figures")
    args = p.parse_args()

    if args.instance == "small":
        problem = build_demo_small()
    elif args.instance == "eight":
        problem = build_demo_eight()
    else:
        problem = build_demo_medium()
    out = os.path.abspath(args.out)
    ensure_out_dir(out)

    results = run_all(problem, max_expansions=args.max_expansions)

    summary_lines = []
    for name, res in results.items():
        ok = res.goal_state is not None
        summary_lines.append(
            f"  {name}: goal={'yes' if ok else 'no'}, "
            f"path_cost={res.path_cost}, expanded={res.nodes_expanded}, "
            f"max_frontier={res.max_frontier}"
        )

    print("Problem:", args.instance, "| courses:", len(problem.courses))
    print("\n".join(summary_lines))

    plot_algorithm_comparison(results, os.path.join(out, "compare_expansions.png"))

    for name, res in results.items():
        if res.goal_state is not None:
            plot_timetable(
                problem,
                res.goal_state,
                f"{name} (cost={res.path_cost:.1f})",
                os.path.join(out, f"timetable_{name}.png"),
            )
        plot_search_trace(
            res.steps,
            name,
            os.path.join(out, f"trace_{name}.png"),
        )
        if res.steps and res.steps[0].h is not None:
            plot_heuristic_trace(
                res.steps,
                name,
                os.path.join(out, f"heuristic_{name}.png"),
            )

    print(f"\nFigures written to: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
