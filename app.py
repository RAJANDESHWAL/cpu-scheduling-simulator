"""
app.py
======

Flask backend for the CPU Task Scheduler Simulator.

Routes
------
GET  /              -> the single-page website
POST /api/schedule  -> run ONE algorithm on the submitted process list
POST /api/compare   -> run all four algorithms on the same process list

All request validation happens here so the scheduling modules can stay pure
and simple.  Errors are returned as JSON with HTTP status 400 and are shown
inline by the frontend (never with alert()).
"""

import re

from flask import Flask, jsonify, render_template, request

from scheduler.algorithms import ALGORITHM_LABELS, run_algorithm
from scheduler.metrics import calculate_metrics, find_best_algorithms

app = Flask(__name__)

# Keep JSON keys in the order we build them (easier to read while debugging).
app.json.sort_keys = False

ALLOWED_ALGORITHMS = ("fcfs", "sjf", "rr", "priority")
MAX_PROCESSES = 100
PID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,16}$")


class ValidationError(ValueError):
    """Raised when the submitted process list or settings are invalid."""


def error_response(message, status=400):
    """Return a consistent JSON error body."""
    return jsonify({"error": message}), status


def parse_int(value, field_label):
    """
    Convert a JSON value to a whole number, or raise a clear error.

    Only integers (or strings containing an integer) are accepted.  Floats
    such as 2.5 or 2.0 are rejected because this simulator uses discrete time
    units.  ``True``/``False`` are rejected even though Python treats them as
    integers.
    """
    if value is None:
        raise ValidationError(f"{field_label} is required.")
    if isinstance(value, bool):
        raise ValidationError(f"{field_label} must be a whole number.")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            raise ValidationError(f"{field_label} is required.")
        if not re.fullmatch(r"[+-]?\d+", text):
            raise ValidationError(f"{field_label} must be a whole number.")
        return int(text)
    raise ValidationError(f"{field_label} must be a whole number.")


def validate_quantum(raw_quantum):
    """Validate the Round Robin time quantum (must be a whole number > 0)."""
    quantum = parse_int(raw_quantum, "Time quantum")
    if quantum <= 0:
        raise ValidationError("Time quantum must be greater than 0.")
    return quantum


def validate_processes(raw_processes):
    """
    Validate and normalise the list of processes submitted by the browser.

    Checks performed
    ----------------
    * the list exists, is a JSON array, is not empty and has <= 100 items
    * each item is an object with PID / arrival / burst / priority
    * PID is 1-16 letters, digits, hyphens or underscores and not "Idle"
    * PIDs are unique (case-insensitive)
    * arrival >= 0, burst > 0, priority >= 0
    * every time value is a whole number

    Returns a new list of clean dictionaries; the caller's data is untouched.
    """
    if raw_processes is None:
        raise ValidationError("No process list was received. Add at least one process.")
    if not isinstance(raw_processes, list):
        raise ValidationError("The process list must be an array of processes.")
    if len(raw_processes) == 0:
        raise ValidationError("Add at least one process before running the simulation.")
    if len(raw_processes) > MAX_PROCESSES:
        raise ValidationError(f"A maximum of {MAX_PROCESSES} processes is supported.")

    cleaned = []
    seen_pids = set()

    for index, item in enumerate(raw_processes, start=1):
        if not isinstance(item, dict):
            raise ValidationError(f"Process #{index} must be an object.")

        raw_pid = item.get("pid")
        if not isinstance(raw_pid, str) or raw_pid.strip() == "":
            raise ValidationError(f"Process #{index}: Process ID is required.")

        pid = raw_pid.strip()
        if not PID_PATTERN.fullmatch(pid):
            raise ValidationError(
                f"Process ID '{pid}' is invalid. Use 1-16 letters, numbers, hyphens or underscores."
            )
        if pid.casefold() == "idle":
            raise ValidationError(
                "The Process ID 'Idle' is reserved for idle CPU time. Choose another ID."
            )
        if pid.casefold() in seen_pids:
            raise ValidationError(f"Duplicate Process ID '{pid}'. Every process needs a unique ID.")
        seen_pids.add(pid.casefold())

        arrival = parse_int(item.get("arrival"), f"Process '{pid}': Arrival time")
        burst = parse_int(item.get("burst"), f"Process '{pid}': Burst time")
        priority = parse_int(item.get("priority"), f"Process '{pid}': Priority")

        if arrival < 0:
            raise ValidationError(f"Process '{pid}': Arrival time cannot be negative.")
        if burst <= 0:
            raise ValidationError(f"Process '{pid}': Burst time must be greater than 0.")
        if priority < 0:
            raise ValidationError(f"Process '{pid}': Priority cannot be negative.")

        cleaned.append(
            {
                "pid": pid,
                "arrival": arrival,
                "burst": burst,
                "priority": priority,
            }
        )

    return cleaned


def read_request_body():
    """Read a JSON object from the request body or raise a clear error."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Send a JSON object with a 'processes' array.")
    return data


@app.get("/")
def index():
    """Serve the single-page simulator."""
    return render_template("index.html")


@app.post("/api/schedule")
def api_schedule():
    """
    Run one scheduling algorithm.

    Request body::

        {
          "processes": [
            {"pid": "P1", "arrival": 0, "burst": 4, "priority": 2}
          ],
          "algorithm": "rr",
          "quantum": 2
        }

    ``quantum`` is required only when algorithm is "rr".
    """
    try:
        data = read_request_body()
        processes = validate_processes(data.get("processes"))

        algorithm_key = str(data.get("algorithm", "")).strip().lower()
        if algorithm_key not in ALLOWED_ALGORITHMS:
            raise ValidationError(
                "Choose a valid algorithm: fcfs, sjf, rr or priority."
            )

        quantum = validate_quantum(data.get("quantum")) if algorithm_key == "rr" else None

        schedule = run_algorithm(algorithm_key, processes, quantum)
        result = calculate_metrics(schedule)
        return jsonify(result), 200

    except ValidationError as exc:
        return error_response(str(exc))
    except ValueError as exc:
        # Defensive: the algorithms module also rejects impossible settings.
        return error_response(str(exc))


@app.post("/api/compare")
def api_compare():
    """
    Run FCFS, SJF, Round Robin and Priority on the SAME process list.

    The time quantum is required because Round Robin is always included.
    The response also reports the best algorithm(s) for each metric.
    """
    try:
        data = read_request_body()
        processes = validate_processes(data.get("processes"))
        quantum = validate_quantum(data.get("quantum"))

        results = []
        for algorithm_key in ALLOWED_ALGORITHMS:
            schedule = run_algorithm(
                algorithm_key,
                processes,
                quantum if algorithm_key == "rr" else None,
            )
            result = calculate_metrics(schedule)
            results.append(
                {
                    "algorithm_key": algorithm_key,
                    "algorithm": ALGORITHM_LABELS[algorithm_key],
                    "quantum": result["quantum"],
                    "metrics": result["metrics"],
                }
            )

        return (
            jsonify(
                {
                    "process_count": len(processes),
                    "quantum": quantum,
                    "results": results,
                    "best": find_best_algorithms(results),
                }
            ),
            200,
        )

    except ValidationError as exc:
        return error_response(str(exc))
    except ValueError as exc:
        return error_response(str(exc))


if __name__ == "__main__":
    # Debug mode gives helpful error pages while developing in VS Code.
    # Open http://127.0.0.1:5000 in the browser.
    app.run(host="127.0.0.1", port=5000, debug=True)
