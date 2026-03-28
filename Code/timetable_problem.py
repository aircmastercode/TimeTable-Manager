"""
Timetable search problem (L3 formulation from planning doc).
State: partial mapping course_index -> (room_index, timeslot_index).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, List, Optional, Set, Tuple

Assignment = Tuple[int, int, int]  # (course_idx, room_idx, timeslot_idx)
State = FrozenSet[Assignment]


@dataclass(frozen=True)
class Course:
    name: str
    instructor_id: int
    enrollment: int
    preferred_slots: FrozenSet[int]


@dataclass(frozen=True)
class Room:
    name: str
    capacity: int


@dataclass
class TimetableProblem:
    courses: List[Course]
    rooms: List[Room]
    num_timeslots: int
    periods_per_day: int

    def slot_day(self, t: int) -> int:
        return t // self.periods_per_day

    def assigned_course_indices(self, state: State) -> Set[int]:
        return {a[0] for a in state}

    def next_course_index(self, state: State) -> Optional[int]:
        assigned = self.assigned_course_indices(state)
        for i in range(len(self.courses)):
            if i not in assigned:
                return i
        return None

    def is_goal(self, state: State) -> bool:
        if len(state) != len(self.courses):
            return False
        return self.hard_violations(state) == 0

    def hard_violations(self, state: State) -> int:
        """Count hard constraint violations (0 = valid partial/full schedule)."""
        by_room_time: dict[Tuple[int, int], int] = {}
        by_inst_time: dict[Tuple[int, int], int] = {}
        bad = 0
        for c_idx, r_idx, t in state:
            c = self.courses[c_idx]
            rt = (r_idx, t)
            if rt in by_room_time:
                bad += 1
            else:
                by_room_time[rt] = c_idx
            it = (c.instructor_id, t)
            if it in by_inst_time:
                bad += 1
            else:
                by_inst_time[it] = c_idx
            if self.rooms[r_idx].capacity < c.enrollment:
                bad += 1
        return bad

    @staticmethod
    def _occupancy(state: State, courses: List[Course]) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
        room_time: Set[Tuple[int, int]] = set()
        inst_time: Set[Tuple[int, int]] = set()
        for oc, or_, ot in state:
            room_time.add((or_, ot))
            inst_time.add((courses[oc].instructor_id, ot))
        return room_time, inst_time

    def can_assign_fast(
        self,
        c_idx: int,
        r_idx: int,
        t: int,
        room_time: Set[Tuple[int, int]],
        inst_time: Set[Tuple[int, int]],
    ) -> bool:
        c = self.courses[c_idx]
        if self.rooms[r_idx].capacity < c.enrollment:
            return False
        if (r_idx, t) in room_time:
            return False
        if (c.instructor_id, t) in inst_time:
            return False
        return True

    def can_assign(self, state: State, c_idx: int, r_idx: int, t: int) -> bool:
        rt, it = self._occupancy(state, self.courses)
        return self.can_assign_fast(c_idx, r_idx, t, rt, it)

    def successors(self, state: State) -> List[Tuple[int, int, int, State]]:
        """Legal actions: assign next unscheduled course to (r,t). Returns list of (c,r,t,new_state)."""
        nc = self.next_course_index(state)
        if nc is None:
            return []
        room_time, inst_time = self._occupancy(state, self.courses)
        out: List[Tuple[int, int, int, State]] = []
        for r_idx in range(len(self.rooms)):
            for t in range(self.num_timeslots):
                if not self.can_assign_fast(nc, r_idx, t, room_time, inst_time):
                    continue
                new_a = (nc, r_idx, t)
                out.append((nc, r_idx, t, frozenset(state | {new_a})))
        return out


def build_demo_small() -> TimetableProblem:
    """
    Default small instance: finishes quickly for UCS / A* / plots (5 courses).
    """
    courses = [
        Course("CS101", 0, 40, frozenset({0, 1, 2})),
        Course("CS102", 0, 35, frozenset({3, 4, 5})),
        Course("MA201", 1, 50, frozenset({0, 3, 6})),
        Course("PH150", 2, 30, frozenset({1, 4, 7})),
        Course("EC210", 3, 60, frozenset({2, 5, 8})),
    ]
    rooms = [
        Room("A101", 80),
        Room("A102", 50),
        Room("Lab1", 45),
    ]
    return TimetableProblem(
        courses=courses,
        rooms=rooms,
        num_timeslots=9,
        periods_per_day=3,
    )


def build_demo_eight() -> TimetableProblem:
    """Eight courses on 12 slots — DFS is fast; UCS/A* may need a high expansion limit."""
    courses = [
        Course("CS101", 0, 40, frozenset({0, 1, 4, 5})),
        Course("CS102", 0, 35, frozenset({2, 3, 6, 7})),
        Course("MA201", 1, 50, frozenset({0, 1, 8, 9})),
        Course("MA202", 1, 45, frozenset({4, 5, 10, 11})),
        Course("PH150", 2, 30, frozenset({0, 4, 8})),
        Course("PH151", 2, 28, frozenset({1, 5, 9})),
        Course("EC210", 3, 60, frozenset({2, 6, 10})),
        Course("EC211", 3, 55, frozenset({3, 7, 11})),
    ]
    rooms = [
        Room("A101", 80),
        Room("A102", 50),
        Room("Lab1", 40),
        Room("Hall", 120),
    ]
    return TimetableProblem(
        courses=courses,
        rooms=rooms,
        num_timeslots=12,
        periods_per_day=4,
    )


def build_demo_medium() -> TimetableProblem:
    """More courses (L3-style); may be heavy for UCS/A* without limits."""
    base = build_demo_eight()
    extra_names_inst = [
        ("CY301", 4, 25, {0, 2, 4}),
        ("CY302", 4, 22, {1, 3, 5}),
        ("BT220", 5, 35, {6, 7, 8}),
        ("BT221", 5, 32, {9, 10, 11}),
        ("HS100", 6, 100, {0, 4, 8}),
        ("HS101", 6, 90, {1, 5, 9}),
        ("ME200", 7, 45, {2, 6, 10}),
        ("ME201", 7, 42, {3, 7, 11}),
    ]
    more = list(base.courses)
    for name, inst, enr, pref in extra_names_inst:
        more.append(
            Course(name, inst, enr, frozenset(pref)),
        )
    return TimetableProblem(
        courses=more,
        rooms=base.rooms,
        num_timeslots=12,
        periods_per_day=4,
    )
