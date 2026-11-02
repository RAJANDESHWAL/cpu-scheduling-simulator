"""
tests/test_algorithms.py
========================

Automated tests for the scheduling engine and the Flask JSON API.

Run from the project folder:

    python -m pytest -v

Every expected number below was also calculated by hand; the comments show
the intermediate completion/turnaround values so the tests are easy to
explain during a viva.
"""

import sys
from pathlib import Path

import pytest

# Make the project root importable when pytest is started from any folder.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app as flask_app
from scheduler.algorithms import (
    IDLE_PID,
    fcfs,
    merge_timeline,
    pid_sort_key,
    priority_scheduling,
    round_robin,
    run_algorithm,
    sjf,
    srtf,
)
from scheduler.metrics import calculate_metrics, find_best_algorithms

# ---------------------------------------------------------------------------
# Shared data
# ---------------------------------------------------------------------------

SAMPLE = [
    {"pid": "P1", "arrival": 0, "burst": 4, "priority": 2},
    {"pid": "P2", "arrival": 1, "burst": 3, "priority": 1},
    {"pid": "P3", "arrival": 2, "burst": 1, "priority": 3},
    {"pid": "P4", "arrival": 3, "burst": 2, "priority": 2},
    {"pid": "P5", "arrival": 4, "burst": 5, "priority": 4},
]

IDLE_CASE = [
    {"pid": "P1", "arrival": 0, "burst": 2, "priority": 1},
    {"pid": "P2", "arrival": 5, "burst": 3, "priority": 2},
    {"pid": "P3", "arrival": 6, "burst": 1, "priority": 3},
]


def timeline_of(result):
    """Convert the result timeline to compact (pid, start, end) tuples."""
    return [(block["pid"], block["start"], block["end"]) for block in result["timeline"]]


def by_pid(result):
    """Index the per-process rows by PID for readable assertions."""
    return {process["pid"]: process for process in result["processes"]}


def all_results(processes, quantum=2):
    """Run all five algorithms and attach metrics."""
    keys = ("fcfs", "sjf", "srtf", "rr", "priority")
    return [
        calculate_metrics(
            run_algorithm(key, processes, quantum if key == "rr" else None)
        )
        for key in keys
    ]


# ---------------------------------------------------------------------------
# Natural PID ordering
# ---------------------------------------------------------------------------


def test_pid_sort_key_orders_numbers_naturally():
    assert sorted(["P10", "P2", "P1"], key=pid_sort_key) == ["P1", "P2", "P10"]
    assert sorted(["10", "2", "1"], key=pid_sort_key) == ["1", "2", "10"]


def test_merge_timeline_joins_only_touching_blocks_of_same_process():
    timeline = [
        {"pid": "P1", "start": 0, "end": 2},
        {"pid": "P1", "start": 2, "end": 4},
        {"pid": "P2", "start": 4, "end": 5},
        {"pid": "P1", "start": 5, "end": 6},
    ]
    assert merge_timeline(timeline) == [
        {"pid": "P1", "start": 0, "end": 4},
        {"pid": "P2", "start": 4, "end": 5},
        {"pid": "P1", "start": 5, "end": 6},
    ]


# ---------------------------------------------------------------------------
# Main sample: FCFS, SJF, Priority
# ---------------------------------------------------------------------------


def test_fcfs_sample():
    result = calculate_metrics(fcfs(SAMPLE))

    assert timeline_of(result) == [
        ("P1", 0, 4),
        ("P2", 4, 7),
        ("P3", 7, 8),
        ("P4", 8, 10),
        ("P5", 10, 15),
    ]

    rows = by_pid(result)
    assert [rows[pid]["completion_time"] for pid in ("P1", "P2", "P3", "P4", "P5")] == [4, 7, 8, 10, 15]
    # TAT = 4, 6, 6, 7, 11 -> 34 / 5 = 6.8
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(6.8)
    # WT = 0, 3, 5, 5, 6 -> 19 / 5 = 3.8
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(3.8)
    # RT = 0, 3, 5, 5, 6 -> 19 / 5 = 3.8
    assert result["metrics"]["avg_response_time"] == pytest.approx(3.8)
    assert result["metrics"]["cpu_utilization"] == pytest.approx(100.0)


def test_sjf_sample():
    result = calculate_metrics(sjf(SAMPLE))

    # P3 (burst 1) runs before P4 (2), P2 (3) and P5 (5).
    assert timeline_of(result) == [
        ("P1", 0, 4),
        ("P3", 4, 5),
        ("P4", 5, 7),
        ("P2", 7, 10),
        ("P5", 10, 15),
    ]

    rows = by_pid(result)
    assert [rows[pid]["completion_time"] for pid in ("P1", "P2", "P3", "P4", "P5")] == [4, 10, 5, 7, 15]
    # TAT = 4, 9, 3, 4, 11 -> 31 / 5 = 6.2
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(6.2)
    # WT = 0, 6, 2, 2, 6 -> 16 / 5 = 3.2
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(3.2)
    # Non-preemptive, so RT = WT = 3.2
    assert result["metrics"]["avg_response_time"] == pytest.approx(3.2)
    assert result["metrics"]["cpu_utilization"] == pytest.approx(100.0)


def test_srtf_sample():
    result = calculate_metrics(srtf(SAMPLE))

    # P3 (remaining 1) preempts P1 at t=2.  At t=3, P1 and P4 both have
    # remaining 2, so P1 continues because it arrived earlier.
    assert timeline_of(result) == [
        ("P1", 0, 2),
        ("P3", 2, 3),
        ("P1", 3, 5),
        ("P4", 5, 7),
        ("P2", 7, 10),
        ("P5", 10, 15),
    ]

    rows = by_pid(result)
    assert [rows[pid]["completion_time"] for pid in ("P1", "P2", "P3", "P4", "P5")] == [5, 10, 3, 7, 15]
    # TAT = 5, 9, 1, 4, 11 -> 30 / 5 = 6.0
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(6.0)
    # WT = 1, 6, 0, 2, 6 -> 15 / 5 = 3.0
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(3.0)
    # RT = 0, 6, 0, 2, 6 -> 14 / 5 = 2.8
    assert result["metrics"]["avg_response_time"] == pytest.approx(2.8)
    assert result["metrics"]["cpu_utilization"] == pytest.approx(100.0)


def test_srtf_preempts_when_shorter_process_arrives():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 7, "priority": 1},
        {"pid": "P2", "arrival": 2, "burst": 2, "priority": 2},
    ]
    result = calculate_metrics(srtf(processes))

    # P1 has 5 units left at t=2; P2 needs only 2, so P2 preempts it.
    assert timeline_of(result) == [
        ("P1", 0, 2),
        ("P2", 2, 4),
        ("P1", 4, 9),
    ]
    rows = by_pid(result)
    assert rows["P1"]["completion_time"] == 9
    assert rows["P2"]["completion_time"] == 4
    assert rows["P2"]["start_time"] == 2
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(5.5)
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(1.0)
    assert result["metrics"]["avg_response_time"] == pytest.approx(0.0)


def test_srtf_equal_remaining_time_does_not_preempt_earlier_process():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 4, "priority": 1},
        {"pid": "P2", "arrival": 2, "burst": 2, "priority": 2},
    ]
    result = calculate_metrics(srtf(processes))

    # At t=2 both have 2 units left.  P1 arrived earlier, so it continues.
    assert timeline_of(result) == [
        ("P1", 0, 4),
        ("P2", 4, 6),
    ]
    rows = by_pid(result)
    assert rows["P1"]["completion_time"] == 4
    assert rows["P2"]["completion_time"] == 6
    assert rows["P2"]["start_time"] == 4
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(4.0)
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(1.0)
    assert result["metrics"]["avg_response_time"] == pytest.approx(1.0)


def test_srtf_simultaneous_arrivals_use_remaining_then_pid():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 4, "priority": 1},
        {"pid": "P2", "arrival": 0, "burst": 4, "priority": 2},
        {"pid": "P3", "arrival": 0, "burst": 2, "priority": 3},
    ]
    result = calculate_metrics(srtf(processes))

    # P3 is shortest.  Then P1 and P2 tie on remaining time and arrival,
    # so the smaller PID P1 runs before P2.
    assert timeline_of(result) == [
        ("P3", 0, 2),
        ("P1", 2, 6),
        ("P2", 6, 10),
    ]
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(6.0)
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(8 / 3)
    assert result["metrics"]["avg_response_time"] == pytest.approx(8 / 3)


def test_srtf_idle_gap_and_resumption():
    result = calculate_metrics(srtf(IDLE_CASE))

    # P2 starts at t=5, but P3 arrives at t=6 with 1 unit left and preempts it.
    assert timeline_of(result) == [
        ("P1", 0, 2),
        (IDLE_PID, 2, 5),
        ("P2", 5, 6),
        ("P3", 6, 7),
        ("P2", 7, 9),
    ]
    rows = by_pid(result)
    assert rows["P1"]["completion_time"] == 2
    assert rows["P2"]["completion_time"] == 9
    assert rows["P3"]["completion_time"] == 7
    # TAT = 2, 4, 1 -> 7/3; WT = 0, 1, 0 -> 1/3; all first starts equal
    # their arrival times, so RT = 0.
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(7 / 3)
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(1 / 3)
    assert result["metrics"]["avg_response_time"] == pytest.approx(0.0)
    assert result["metrics"]["cpu_utilization"] == pytest.approx(200 / 3)


def test_priority_sample():
    result = calculate_metrics(priority_scheduling(SAMPLE))

    # P2 (priority 1) runs before P4 (2), P3 (3), P5 (4).
    assert timeline_of(result) == [
        ("P1", 0, 4),
        ("P2", 4, 7),
        ("P4", 7, 9),
        ("P3", 9, 10),
        ("P5", 10, 15),
    ]

    rows = by_pid(result)
    assert [rows[pid]["completion_time"] for pid in ("P1", "P2", "P3", "P4", "P5")] == [4, 7, 10, 9, 15]
    # TAT = 4, 6, 8, 6, 11 -> 35 / 5 = 7.0
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(7.0)
    # WT = 0, 3, 7, 4, 6 -> 20 / 5 = 4.0
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(4.0)
    assert result["metrics"]["avg_response_time"] == pytest.approx(4.0)
    assert result["metrics"]["cpu_utilization"] == pytest.approx(100.0)


# ---------------------------------------------------------------------------
# Round Robin
# ---------------------------------------------------------------------------


def test_round_robin_sample():
    result = calculate_metrics(round_robin(SAMPLE, 2))

    assert timeline_of(result) == [
        ("P1", 0, 2),
        ("P2", 2, 4),
        ("P3", 4, 5),
        ("P1", 5, 7),
        ("P4", 7, 9),
        ("P5", 9, 11),
        ("P2", 11, 12),
        ("P5", 12, 15),
    ]

    rows = by_pid(result)
    assert [rows[pid]["completion_time"] for pid in ("P1", "P2", "P3", "P4", "P5")] == [7, 12, 5, 9, 15]
    # TAT = 7, 11, 3, 6, 11 -> 38 / 5 = 7.6
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(7.6)
    # WT = 3, 8, 2, 4, 6 -> 23 / 5 = 4.6
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(4.6)
    # RT = (0-0), (2-1), (4-2), (7-3), (9-4) = 0,1,2,4,5 -> 12 / 5 = 2.4
    assert result["metrics"]["avg_response_time"] == pytest.approx(2.4)
    assert result["metrics"]["cpu_utilization"] == pytest.approx(100.0)


def test_round_robin_arrival_at_expiry_enters_before_preempted_process():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 3, "priority": 1},
        {"pid": "P2", "arrival": 2, "burst": 1, "priority": 2},
    ]
    result = calculate_metrics(round_robin(processes, 2))

    # At t=2, P2 arrives exactly when P1's quantum expires.  P2 must run
    # before P1 is put back on the queue.
    assert timeline_of(result) == [
        ("P1", 0, 2),
        ("P2", 2, 3),
        ("P1", 3, 4),
    ]
    rows = by_pid(result)
    assert rows["P1"]["completion_time"] == 4
    assert rows["P2"]["completion_time"] == 3
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(2.5)
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(0.5)
    assert result["metrics"]["avg_response_time"] == pytest.approx(0.0)


def test_round_robin_merges_consecutive_blocks():
    processes = [{"pid": "P1", "arrival": 0, "burst": 5, "priority": 1}]
    result = calculate_metrics(round_robin(processes, 2))

    # Internally P1 runs 0-2, 2-4, 4-5.  The displayed Gantt chart merges them.
    assert timeline_of(result) == [("P1", 0, 5)]
    assert result["metrics"]["cpu_utilization"] == pytest.approx(100.0)


def test_round_robin_quantum_larger_than_every_burst_matches_fcfs():
    rr_result = calculate_metrics(round_robin(SAMPLE, 100))
    fcfs_result = calculate_metrics(fcfs(SAMPLE))

    assert timeline_of(rr_result) == timeline_of(fcfs_result)
    assert rr_result["metrics"] == fcfs_result["metrics"]


def test_round_robin_quantum_one():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 2, "priority": 1},
        {"pid": "P2", "arrival": 1, "burst": 2, "priority": 2},
    ]
    result = calculate_metrics(round_robin(processes, 1))

    assert timeline_of(result) == [
        ("P1", 0, 1),
        ("P2", 1, 2),
        ("P1", 2, 3),
        ("P2", 3, 4),
    ]
    rows = by_pid(result)
    assert rows["P1"]["completion_time"] == 3
    assert rows["P2"]["completion_time"] == 4
    # TAT = 3, 3 -> 3.0; WT = 1, 1 -> 1.0; RT = 0, 0 -> 0.0
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(3.0)
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(1.0)
    assert result["metrics"]["avg_response_time"] == pytest.approx(0.0)


def test_round_robin_rejects_invalid_quantum():
    with pytest.raises(ValueError):
        round_robin(SAMPLE, 0)
    with pytest.raises(ValueError):
        round_robin(SAMPLE, -1)
    with pytest.raises(ValueError):
        run_algorithm("rr", SAMPLE)


# ---------------------------------------------------------------------------
# Idle time and CPU utilization
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("algorithm", [fcfs, sjf, priority_scheduling])
def test_idle_gap_non_preemptive(algorithm):
    result = calculate_metrics(algorithm(IDLE_CASE))

    assert timeline_of(result) == [
        ("P1", 0, 2),
        (IDLE_PID, 2, 5),
        ("P2", 5, 8),
        ("P3", 8, 9),
    ]
    rows = by_pid(result)
    # TAT = 2, 3, 3 -> 8/3; WT = 0, 0, 2 -> 2/3; RT = 0, 0, 2 -> 2/3
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(8 / 3)
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(2 / 3)
    assert result["metrics"]["avg_response_time"] == pytest.approx(2 / 3)
    # Busy 6 / elapsed 9 = 66.67%; the 3-unit idle gap is excluded.
    assert result["metrics"]["busy_time"] == 6
    assert result["metrics"]["idle_time"] == 3
    assert result["metrics"]["total_time"] == 9
    assert result["metrics"]["cpu_utilization"] == pytest.approx(200 / 3)


def test_idle_gap_round_robin():
    result = calculate_metrics(round_robin(IDLE_CASE, 2))

    assert timeline_of(result) == [
        ("P1", 0, 2),
        (IDLE_PID, 2, 5),
        ("P2", 5, 7),
        ("P3", 7, 8),
        ("P2", 8, 9),
    ]
    rows = by_pid(result)
    assert rows["P1"]["completion_time"] == 2
    assert rows["P2"]["completion_time"] == 9
    assert rows["P3"]["completion_time"] == 8
    # TAT = 2, 4, 2 -> 8/3; WT = 0, 1, 1 -> 2/3; RT = 0, 0, 1 -> 1/3
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(8 / 3)
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(2 / 3)
    assert result["metrics"]["avg_response_time"] == pytest.approx(1 / 3)
    assert result["metrics"]["cpu_utilization"] == pytest.approx(200 / 3)


def test_single_process_with_initial_idle():
    processes = [{"pid": "P1", "arrival": 3, "burst": 4, "priority": 1}]

    for result in all_results(processes, quantum=2):
        assert timeline_of(result) == [(IDLE_PID, 0, 3), ("P1", 3, 7)]
        assert result["metrics"]["total_time"] == 7
        assert result["metrics"]["busy_time"] == 4
        assert result["metrics"]["idle_time"] == 3
        assert result["metrics"]["cpu_utilization"] == pytest.approx(400 / 7)
        assert result["metrics"]["avg_turnaround_time"] == pytest.approx(4.0)
        assert result["metrics"]["avg_waiting_time"] == pytest.approx(0.0)
        assert result["metrics"]["avg_response_time"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Tie-breaking and simultaneous arrivals
# ---------------------------------------------------------------------------


def test_sjf_equal_burst_tie_uses_arrival_then_pid():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 5, "priority": 2},
        {"pid": "P2", "arrival": 1, "burst": 2, "priority": 3},
        {"pid": "P3", "arrival": 1, "burst": 2, "priority": 1},
    ]
    result = calculate_metrics(sjf(processes))

    # Both P2 and P3 have burst 2 and arrival 1, so the smaller PID wins.
    assert timeline_of(result) == [("P1", 0, 5), ("P2", 5, 7), ("P3", 7, 9)]
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(19 / 3)
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(10 / 3)
    assert result["metrics"]["avg_response_time"] == pytest.approx(10 / 3)


def test_priority_tie_ignores_burst_and_uses_pid():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 3, "priority": 2},
        {"pid": "P2", "arrival": 1, "burst": 2, "priority": 1},
        {"pid": "P3", "arrival": 1, "burst": 1, "priority": 1},
    ]
    result = calculate_metrics(priority_scheduling(processes))

    # P2 and P3 both have priority 1 and arrival 1.  P2 wins despite the
    # longer burst, because priority scheduling does not compare bursts.
    assert timeline_of(result) == [("P1", 0, 3), ("P2", 3, 5), ("P3", 5, 6)]
    assert result["metrics"]["avg_turnaround_time"] == pytest.approx(4.0)
    assert result["metrics"]["avg_waiting_time"] == pytest.approx(2.0)
    assert result["metrics"]["avg_response_time"] == pytest.approx(2.0)


def test_fcfs_simultaneous_arrivals_are_sorted_by_pid():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 2, "priority": 3},
        {"pid": "P2", "arrival": 0, "burst": 1, "priority": 1},
        {"pid": "P3", "arrival": 0, "burst": 1, "priority": 2},
    ]
    result = calculate_metrics(fcfs(processes))

    assert timeline_of(result) == [("P1", 0, 2), ("P2", 2, 3), ("P3", 3, 4)]


def test_sjf_and_priority_simultaneous_arrivals():
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 2, "priority": 3},
        {"pid": "P2", "arrival": 0, "burst": 1, "priority": 1},
        {"pid": "P3", "arrival": 0, "burst": 1, "priority": 2},
    ]

    sjf_timeline = timeline_of(calculate_metrics(sjf(processes)))
    priority_timeline = timeline_of(calculate_metrics(priority_scheduling(processes)))

    # SJF: equal bursts for P2/P3 -> smaller PID P2 first, then P3, then P1.
    assert sjf_timeline == [("P2", 0, 1), ("P3", 1, 2), ("P1", 2, 4)]
    # Priority: 1 (P2), 2 (P3), 3 (P1).
    assert priority_timeline == [("P2", 0, 1), ("P3", 1, 2), ("P1", 2, 4)]


# ---------------------------------------------------------------------------
# Comparison helper
# ---------------------------------------------------------------------------


def test_find_best_algorithms_on_sample():
    results = all_results(SAMPLE, quantum=2)
    best = find_best_algorithms(results)

    assert best["avg_turnaround_time"] == ["SRTF"]
    assert best["avg_waiting_time"] == ["SRTF"]
    # Round Robin responds to new processes sooner: 2.4 vs SRTF's 2.8.
    assert best["avg_response_time"] == ["Round Robin"]
    assert best["cpu_utilization"] == ["FCFS", "SJF", "SRTF", "Round Robin", "Priority"]


def test_find_best_algorithms_keeps_ties():
    results = [
        {"algorithm": "A", "metrics": {"avg_turnaround_time": 3.0, "avg_waiting_time": 1.0, "avg_response_time": 1.0, "cpu_utilization": 100.0}},
        {"algorithm": "B", "metrics": {"avg_turnaround_time": 3.0, "avg_waiting_time": 2.0, "avg_response_time": 0.5, "cpu_utilization": 100.0}},
    ]
    best = find_best_algorithms(results)

    assert best["avg_turnaround_time"] == ["A", "B"]
    assert best["avg_waiting_time"] == ["A"]
    assert best["avg_response_time"] == ["B"]
    assert best["cpu_utilization"] == ["A", "B"]


# ---------------------------------------------------------------------------
# Flask API tests (test client; no server needed for these)
# ---------------------------------------------------------------------------


@pytest.fixture()
def client():
    flask_app.app.config.update(TESTING=True)
    with flask_app.app.test_client() as test_client:
        yield test_client


def test_index_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"CPU Scheduler Lab" in response.data
    assert b"Gantt chart" in response.data


def test_static_assets_load(client):
    assert client.get("/static/css/style.css").status_code == 200
    assert client.get("/static/js/main.js").status_code == 200
    assert client.get("/static/js/gantt.js").status_code == 200
    assert client.get("/static/js/charts.js").status_code == 200
    assert client.get("/static/favicon.svg").status_code == 200
    assert client.get("/static/favicon.svg").status_code == 200


def test_api_schedule_fcfs(client):
    response = client.post(
        "/api/schedule",
        json={"processes": SAMPLE, "algorithm": "fcfs"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["algorithm"] == "FCFS"
    assert data["metrics"]["avg_turnaround_time"] == pytest.approx(6.8)
    assert len(data["timeline"]) == 5


def test_api_schedule_round_robin(client):
    response = client.post(
        "/api/schedule",
        json={"processes": SAMPLE, "algorithm": "rr", "quantum": 2},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["quantum"] == 2
    assert data["metrics"]["avg_response_time"] == pytest.approx(2.4)


def test_api_schedule_srtf(client):
    response = client.post(
        "/api/schedule",
        json={"processes": SAMPLE, "algorithm": "srtf"},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["algorithm"] == "SRTF"
    assert data["metrics"]["avg_turnaround_time"] == pytest.approx(6.0)
    assert len(data["timeline"]) == 6


def test_api_compare(client):
    response = client.post(
        "/api/compare",
        json={"processes": SAMPLE, "quantum": 2},
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["process_count"] == 5
    assert data["quantum"] == 2
    assert [item["algorithm"] for item in data["results"]] == [
        "FCFS",
        "SJF",
        "SRTF",
        "Round Robin",
        "Priority",
    ]
    assert data["best"]["avg_turnaround_time"] == ["SRTF"]


@pytest.mark.parametrize(
    "payload,expected_fragment",
    [
        ({"processes": [], "algorithm": "fcfs"}, "at least one process"),
        ({"processes": None, "algorithm": "fcfs"}, "No process list"),
        ({"processes": "not-a-list", "algorithm": "fcfs"}, "array of processes"),
        ({"processes": SAMPLE, "algorithm": "unknown"}, "valid algorithm"),
        ({"processes": SAMPLE, "algorithm": "rr"}, "Time quantum is required"),
        ({"processes": SAMPLE, "algorithm": "rr", "quantum": 0}, "greater than 0"),
    ],
)
def test_api_schedule_rejects_bad_settings(client, payload, expected_fragment):
    response = client.post("/api/schedule", json=payload)
    assert response.status_code == 400
    assert expected_fragment in response.get_json()["error"]


@pytest.mark.parametrize(
    "process,expected_fragment",
    [
        ({"pid": "P1", "arrival": -1, "burst": 2, "priority": 1}, "cannot be negative"),
        ({"pid": "P1", "arrival": 0, "burst": 0, "priority": 1}, "greater than 0"),
        ({"pid": "P1", "arrival": 0, "burst": 2, "priority": -1}, "cannot be negative"),
        ({"pid": "", "arrival": 0, "burst": 2, "priority": 1}, "required"),
        ({"pid": "P1", "arrival": "abc", "burst": 2, "priority": 1}, "whole number"),
        ({"pid": "P1", "arrival": 0, "burst": 2.5, "priority": 1}, "whole number"),
        ({"pid": "P1", "arrival": 0, "burst": 2}, "required"),
        ({"pid": "Idle", "arrival": 0, "burst": 2, "priority": 1}, "reserved"),
        ({"pid": "P 1", "arrival": 0, "burst": 2, "priority": 1}, "invalid"),
    ],
)
def test_api_rejects_invalid_process_fields(client, process, expected_fragment):
    response = client.post(
        "/api/schedule",
        json={"processes": [process], "algorithm": "fcfs"},
    )
    assert response.status_code == 400
    assert expected_fragment in response.get_json()["error"]


def test_api_rejects_duplicate_pids_case_insensitively(client):
    processes = [
        {"pid": "P1", "arrival": 0, "burst": 2, "priority": 1},
        {"pid": "p1", "arrival": 1, "burst": 3, "priority": 2},
    ]
    response = client.post(
        "/api/schedule",
        json={"processes": processes, "algorithm": "fcfs"},
    )
    assert response.status_code == 400
    assert "Duplicate Process ID" in response.get_json()["error"]


def test_api_compare_requires_quantum(client):
    response = client.post("/api/compare", json={"processes": SAMPLE})
    assert response.status_code == 400
    assert "Time quantum is required" in response.get_json()["error"]


def test_api_rejects_non_json_body(client):
    response = client.post("/api/schedule", data="hello", content_type="text/plain")
    assert response.status_code == 400
    assert "JSON object" in response.get_json()["error"]
