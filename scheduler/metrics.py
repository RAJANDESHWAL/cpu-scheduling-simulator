"""
scheduler/metrics.py
====================

Turns a raw scheduling result (timeline + start/completion times) into the
performance metrics shown on the website.

Keeping these calculations in one file guarantees that every algorithm uses
exactly the same formulas:

    TAT = Completion Time - Arrival Time
    WT  = Turnaround Time - Burst Time
    RT  = First CPU Start Time - Arrival Time
    CPU Utilisation = (busy time / elapsed time) * 100

No Flask imports live here either.
"""

from .algorithms import IDLE_PID


def calculate_metrics(schedule):
    """
    Add TAT, WT and RT to each process and compute averages.

    Parameters
    ----------
    schedule : dict
        Output of ``scheduler.algorithms.run_algorithm``.  It contains
        ``timeline`` and ``processes`` (with start/completion times).

    Returns
    -------
    dict
        A copy of the schedule with enriched process rows and a ``metrics``
        dictionary.  The input dictionary is not modified.
    """
    rows = []
    for process in schedule["processes"]:
        turnaround_time = process["completion_time"] - process["arrival"]
        waiting_time = turnaround_time - process["burst"]
        response_time = process["start_time"] - process["arrival"]

        row = dict(process)
        row.update(
            {
                "turnaround_time": turnaround_time,
                "waiting_time": waiting_time,
                "response_time": response_time,
            }
        )
        rows.append(row)

    process_count = len(rows)
    if process_count:
        avg_turnaround = sum(r["turnaround_time"] for r in rows) / process_count
        avg_waiting = sum(r["waiting_time"] for r in rows) / process_count
        avg_response = sum(r["response_time"] for r in rows) / process_count
    else:
        avg_turnaround = avg_waiting = avg_response = 0.0

    timeline = schedule["timeline"]

    # The timeline always starts at time 0, so the last end time is the total
    # elapsed time.  If the first process arrives at time 3, the 0-3 Idle
    # block is included in total_time but excluded from busy_time.
    total_time = timeline[-1]["end"] if timeline else 0
    busy_time = sum(
        block["end"] - block["start"]
        for block in timeline
        if block["pid"] != IDLE_PID
    )
    idle_time = total_time - busy_time
    cpu_utilization = (busy_time / total_time * 100.0) if total_time else 0.0

    result = dict(schedule)
    result["processes"] = rows
    result["metrics"] = {
        "process_count": process_count,
        "avg_turnaround_time": avg_turnaround,
        "avg_waiting_time": avg_waiting,
        "avg_response_time": avg_response,
        "cpu_utilization": cpu_utilization,
        "total_time": total_time,
        "busy_time": busy_time,
        "idle_time": idle_time,
    }
    return result


def find_best_algorithms(results):
    """
    Find the best algorithm for each metric in a comparison.

    Lower is better for TAT, WT and RT.  Higher is better for CPU
    utilisation.  Ties are preserved: every algorithm with the winning value
    is returned in the list.

    Parameters
    ----------
    results : list[dict]
        Items containing at least ``"algorithm"`` and ``"metrics"``.

    Returns
    -------
    dict
        Example::

            {
              "avg_turnaround_time": ["SJF"],
              "avg_waiting_time": ["SJF"],
              "avg_response_time": ["SJF"],
              "cpu_utilization": ["FCFS", "SJF", "Round Robin", "Priority"]
            }
    """
    metrics = (
        ("avg_turnaround_time", False),
        ("avg_waiting_time", False),
        ("avg_response_time", False),
        ("cpu_utilization", True),
    )
    best = {}

    for metric_name, higher_is_better in metrics:
        values = [item["metrics"][metric_name] for item in results]
        if not values:
            best[metric_name] = []
            continue

        target = max(values) if higher_is_better else min(values)
        # A tiny tolerance keeps floating-point ties (e.g. 3.3333333333)
        # from being split into different winners.
        best[metric_name] = [
            item["algorithm"]
            for item in results
            if abs(item["metrics"][metric_name] - target) < 1e-9
        ]

    return best
