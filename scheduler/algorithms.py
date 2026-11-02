"""
scheduler/algorithms.py
=======================

Pure-Python implementations of five single-core CPU scheduling algorithms.

This module has NO Flask imports and NO knowledge of the web page.  Every
function receives a list of process dictionaries and returns a plain Python
dictionary, which makes the scheduling logic easy to test and easy to explain.

A process dictionary looks like this::

    {"pid": "P1", "arrival": 0, "burst": 4, "priority": 2}

The functions assume that the input has already been validated (unique IDs,
non-negative arrival, positive burst, non-negative priority).  Request-level
validation lives in app.py.
"""

from collections import deque
import re

# This label is used for periods when the CPU has no process to run.
# app.py refuses to let a user create a process with this ID.
IDLE_PID = "Idle"

# Human-readable names used in API responses and on the page.
ALGORITHM_LABELS = {
    "fcfs": "FCFS",
    "sjf": "SJF",
    "srtf": "SRTF",
    "rr": "Round Robin",
    "priority": "Priority",
}


def pid_sort_key(pid):
    """
    Return a sort key for a Process ID using natural ordering.

    "P2" sorts before "P10" because the trailing number is compared as an
    integer, not as text.  IDs without a trailing number are compared
    case-insensitively after the numeric IDs.

    Examples
    --------
    >>> sorted(["P10", "P2", "P1"], key=pid_sort_key)
    ['P1', 'P2', 'P10']
    """
    text = str(pid)
    match = re.fullmatch(r"(.*?)(\d+)", text)
    if match:
        prefix, number = match.group(1), match.group(2)
        return (0, prefix.lower(), int(number))
    return (1, text.lower(), 0)


def merge_timeline(timeline):
    """
    Merge adjacent Gantt blocks that belong to the same process.

    Round Robin can give a process two slots in a row when the ready queue is
    empty (for example, a single process run with quantum 2 produces
    0-2, 2-4, 4-5).  The requirement asks for one merged block: 0-5.

    Two blocks are merged only when they touch (previous end == next start)
    and have the same PID, so no time is lost or invented.
    """
    merged = []
    for block in timeline:
        if (
            merged
            and merged[-1]["pid"] == block["pid"]
            and merged[-1]["end"] == block["start"]
        ):
            merged[-1]["end"] = block["end"]
        else:
            merged.append({"pid": block["pid"], "start": block["start"], "end": block["end"]})
    return merged


def _record(process, start, end):
    """Build the per-process result row stored by every algorithm."""
    return {
        "pid": process["pid"],
        "arrival": process["arrival"],
        "burst": process["burst"],
        "priority": process["priority"],
        "start_time": start,
        "completion_time": end,
    }


def _build_result(algorithm_key, processes, records, timeline, quantum=None):
    """
    Assemble the common result structure.

    ``records`` maps a PID to the row created by ``_record``.  Rows are
    returned in the same order as the user's input list, which keeps the
    results table familiar.
    """
    return {
        "algorithm_key": algorithm_key,
        "algorithm": ALGORITHM_LABELS[algorithm_key],
        "quantum": quantum,
        "timeline": merge_timeline(timeline),
        "processes": [records[process["pid"]] for process in processes],
    }


def fcfs(processes):
    """
    First Come, First Served (non-preemptive).

    Processes are sorted by arrival time, then by Process ID for simultaneous
    arrivals.  Each process runs to completion.  If the CPU is idle before the
    next arrival, an "Idle" block is added.
    """
    ordered = sorted(processes, key=lambda p: (p["arrival"], pid_sort_key(p["pid"])))
    timeline = []
    records = {}
    time = 0

    for process in ordered:
        if time < process["arrival"]:
            timeline.append({"pid": IDLE_PID, "start": time, "end": process["arrival"]})
            time = process["arrival"]

        start = time
        time += process["burst"]
        timeline.append({"pid": process["pid"], "start": start, "end": time})
        records[process["pid"]] = _record(process, start, time)

    return _build_result("fcfs", processes, records, timeline)


def _non_preemptive(processes, algorithm_key, key_function):
    """
    Shared engine for SJF and Priority Scheduling.

    Both algorithms repeatedly choose one process from the processes that have
    already arrived and run it to completion.  They differ only in the key:
    SJF uses burst time, Priority uses the priority number.  The key includes
    arrival time and PID so the required tie-breaking is automatic.
    """
    pending = list(processes)
    timeline = []
    records = {}
    time = 0

    while pending:
        available = [p for p in pending if p["arrival"] <= time]

        if not available:
            # Nobody has arrived yet: jump to the next arrival and mark idle.
            next_arrival = min(p["arrival"] for p in pending)
            timeline.append({"pid": IDLE_PID, "start": time, "end": next_arrival})
            time = next_arrival
            continue

        chosen = min(available, key=key_function)
        start = time
        time += chosen["burst"]
        timeline.append({"pid": chosen["pid"], "start": start, "end": time})
        records[chosen["pid"]] = _record(chosen, start, time)
        pending.remove(chosen)

    return _build_result(algorithm_key, processes, records, timeline)


def sjf(processes):
    """
    Shortest Job First (non-preemptive).

    Among arrived processes, the smallest burst time wins.  Equal bursts are
    broken by earlier arrival and then by the smaller Process ID.
    """
    return _non_preemptive(
        processes,
        "sjf",
        lambda p: (p["burst"], p["arrival"], pid_sort_key(p["pid"])),
    )


def srtf(processes):
    """
    Shortest Remaining Time First (preemptive SJF).

    At every arrival the algorithm compares the remaining burst times of all
    arrived, unfinished processes.  The smallest remaining time runs; if a new
    arrival is shorter than the running process, it preempts immediately.

    Ties are broken by earlier arrival time and then by the smaller PID, using
    the same natural PID ordering as the other algorithms.  Because only a new
    arrival can change the winner, the running process can safely execute until
    either it finishes or the next arrival occurs.
    """
    ordered = sorted(processes, key=lambda p: (p["arrival"], pid_sort_key(p["pid"])))
    remaining = {p["pid"]: p["burst"] for p in processes}
    records = {}
    timeline = []
    completed = 0
    time = 0

    while completed < len(processes):
        available = [
            p for p in ordered
            if p["arrival"] <= time and remaining[p["pid"]] > 0
        ]

        if not available:
            # No process has arrived yet: jump to the next arrival.
            next_arrival = min(
                p["arrival"] for p in ordered if remaining[p["pid"]] > 0
            )
            timeline.append({"pid": IDLE_PID, "start": time, "end": next_arrival})
            time = next_arrival
            continue

        chosen = min(
            available,
            key=lambda p: (
                remaining[p["pid"]],
                p["arrival"],
                pid_sort_key(p["pid"]),
            ),
        )
        pid = chosen["pid"]

        if pid not in records:
            records[pid] = _record(chosen, time, None)

        future_arrivals = [
            p["arrival"]
            for p in ordered
            if p["arrival"] > time and remaining[p["pid"]] > 0
        ]
        next_arrival = min(future_arrivals) if future_arrivals else None

        start = time
        if next_arrival is None:
            run_for = remaining[pid]
        else:
            run_for = min(remaining[pid], next_arrival - time)

        time += run_for
        remaining[pid] -= run_for
        timeline.append({"pid": pid, "start": start, "end": time})

        if remaining[pid] == 0:
            records[pid]["completion_time"] = time
            completed += 1

    return _build_result("srtf", processes, records, timeline)


def priority_scheduling(processes):
    """
    Priority Scheduling (non-preemptive, lower number = higher priority).

    Among arrived processes, the smallest priority number wins.  Equal
    priorities are broken by earlier arrival and then by the smaller PID.
    """
    return _non_preemptive(
        processes,
        "priority",
        lambda p: (p["priority"], p["arrival"], pid_sort_key(p["pid"])),
    )


def round_robin(processes, quantum):
    """
    Round Robin (preemptive, fixed time quantum).

    Rules implemented exactly as specified in the project brief:

    * Arrivals at the current time enter the ready queue in arrival/PID order.
    * When a quantum expires, processes that arrive at that exact instant are
      enqueued BEFORE the preempted process is added back.
    * If the ready queue is empty, the CPU is idle until the next arrival.
    * Adjacent blocks of the same process are merged in the Gantt output.
    """
    if not isinstance(quantum, int) or isinstance(quantum, bool) or quantum <= 0:
        raise ValueError("Time quantum must be a whole number greater than 0.")

    ordered = sorted(processes, key=lambda p: (p["arrival"], pid_sort_key(p["pid"])))
    remaining = {p["pid"]: p["burst"] for p in processes}
    records = {}
    timeline = []
    ready = deque()
    next_arrival_index = 0
    completed = 0
    time = 0

    def enqueue_arrivals(until_time):
        """Move every process with arrival <= until_time into the ready queue."""
        nonlocal next_arrival_index
        while (
            next_arrival_index < len(ordered)
            and ordered[next_arrival_index]["arrival"] <= until_time
        ):
            ready.append(ordered[next_arrival_index])
            next_arrival_index += 1

    while completed < len(processes):
        enqueue_arrivals(time)

        if not ready:
            # No process is waiting.  Jump to the next arrival, if any.
            if next_arrival_index >= len(ordered):
                break
            arrival_time = ordered[next_arrival_index]["arrival"]
            timeline.append({"pid": IDLE_PID, "start": time, "end": arrival_time})
            time = arrival_time
            enqueue_arrivals(time)
            continue

        process = ready.popleft()
        pid = process["pid"]
        run_for = min(quantum, remaining[pid])

        if pid not in records:
            records[pid] = _record(process, time, None)

        start = time
        time += run_for
        remaining[pid] -= run_for
        timeline.append({"pid": pid, "start": start, "end": time})

        # New arrivals at this exact time go ahead of the preempted process.
        enqueue_arrivals(time)

        if remaining[pid] > 0:
            ready.append(process)
        else:
            records[pid]["completion_time"] = time
            completed += 1

    return _build_result("rr", processes, records, timeline, quantum=quantum)


def run_algorithm(algorithm_key, processes, quantum=None):
    """
    Dispatcher used by the Flask API and by tests.

    Parameters
    ----------
    algorithm_key : str
        One of "fcfs", "sjf", "srtf", "rr", "priority" (case-insensitive).
    processes : list[dict]
        Validated process dictionaries.
    quantum : int, optional
        Required only for Round Robin.

    Returns
    -------
    dict
        The common result structure with timeline and process start/completion
        times, but without TAT/WT/RT (metrics.py adds those).
    """
    key = str(algorithm_key).strip().lower()

    if key == "fcfs":
        return fcfs(processes)
    if key == "sjf":
        return sjf(processes)
    if key == "srtf":
        return srtf(processes)
    if key == "priority":
        return priority_scheduling(processes)
    if key == "rr":
        if quantum is None:
            raise ValueError("Time quantum is required for Round Robin.")
        return round_robin(processes, quantum)

    raise ValueError(f"Unknown scheduling algorithm: {algorithm_key!r}")
