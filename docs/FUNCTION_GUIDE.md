# Function Guide

This document describes every important function in the project: where it lives, what it does, its parameters and return value, how it works internally, the data structures it uses, and which functions call it.

The scheduling package (`scheduler/`) contains **no Flask code**. This separation is deliberate: the algorithms can be tested from a plain Python shell and explained without mentioning the web server.

---

## 1. Core data structures

Understanding these shapes makes every function below easier to follow.

### 1.1 Input process dictionary

```python
{
    "pid": "P1",       # string, 1-16 letters/digits/_/-, not "Idle"
    "arrival": 0,      # whole number >= 0
    "burst": 4,        # whole number > 0
    "priority": 2      # whole number >= 0, lower number = higher priority
}
```

### 1.2 Gantt timeline block

```python
{"pid": "P1", "start": 0, "end": 2}
```

A special `pid` of `"Idle"` represents a period when no process was ready.

### 1.3 Raw schedule (returned by `scheduler.algorithms`)

```python
{
    "algorithm_key": "rr",
    "algorithm": "Round Robin",
    "quantum": 2,
    "timeline": [ ... timeline blocks ... ],
    "processes": [
        {
            "pid": "P1",
            "arrival": 0,
            "burst": 4,
            "priority": 2,
            "start_time": 0,
            "completion_time": 7
        }
    ]
}
```

### 1.4 Final schedule (returned by `scheduler.metrics.calculate_metrics`)

The same dictionary with three extra fields per process (`turnaround_time`, `waiting_time`, `response_time`) and a new `metrics` dictionary:

```python
"metrics": {
    "process_count": 5,
    "avg_turnaround_time": 7.6,
    "avg_waiting_time": 4.6,
    "avg_response_time": 2.4,
    "cpu_utilization": 100.0,
    "total_time": 15,
    "busy_time": 15,
    "idle_time": 0
}
```

### 1.5 Browser state (`static/js/main.js`)

```javascript
{
    processes: [...],          // array of process objects
    editIndex: null,           // null = add mode, otherwise index being edited
    selectedAlgorithm: "fcfs", // "fcfs" | "sjf" | "srtf" | "rr" | "priority" | "priority_preemptive"
    lastResult: null,          // last /api/schedule response
    lastComparison: null       // last /api/compare response
}
```

### 1.6 Internal algorithm structures

| Structure | Type | Purpose |
|---|---|---|
| `pending` | list of process dicts | Processes not yet completed (SJF / Priority). |
| `ready` | `collections.deque` | Round Robin ready queue; O(1) append/popleft. |
| `remaining` | dict `pid -> int` | Remaining burst time in SRTF, Preemptive Priority and Round Robin. |
| `records` | dict `pid -> result row` | Start/completion times, later ordered into the result list. |
| `timeline` | list of dicts | Gantt blocks in chronological order. |
| `colors` | dict `pid -> hex colour` | Stable colour assignment in `gantt.js`. |
| `charts` | dict `key -> Chart` | Existing Chart.js instances so they can be destroyed before re-render. |

---

## 2. `app.py` — Flask routes and validation

### `class ValidationError(ValueError)`

- **File:** `app.py`
- **Purpose:** A dedicated exception for user input problems.
- **Why subclass `ValueError`:** the routes can catch request validation separately from unexpected programming errors, while still treating both as value errors at the outer level.
- **Used by:** `parse_int`, `validate_quantum`, `validate_processes`, `read_request_body`, both API routes.

### `error_response(message, status=400)`

- **Purpose:** Return a consistent JSON error body and HTTP status.
- **Parameters:** `message` (string shown to the user), `status` (default `400`).
- **Returns:** `(flask.Response, status)` where the body is `{"error": message}`.
- **Internal working:** calls `flask.jsonify`.
- **Called by:** `api_schedule`, `api_compare`.

### `parse_int(value, field_label)`

- **Purpose:** Convert a JSON value into a whole number or raise a clear validation error.
- **Parameters:** `value` (raw JSON value), `field_label` (for example `"Process 'P1': Arrival time"`).
- **Returns:** a Python `int`.
- **Internal working:**
  1. `None` → "required".
  2. `bool` → rejected (Python treats `True` as 1, which would be surprising).
  3. `int` → returned unchanged.
  4. `str` → stripped; empty → required; must match `^[+-]?\d+$`, then converted with `int()`.
  5. Any other type (including a float such as `2.5` or `2.0`) → "must be a whole number".
- **Data structures:** regular expression match only.
- **Calls:** `ValidationError`.
- **Called by:** `validate_quantum`, `validate_processes`.

### `validate_quantum(raw_quantum)`

- **Purpose:** Validate the Round Robin time quantum.
- **Parameters:** raw JSON value.
- **Returns:** `int` greater than zero.
- **Internal working:** calls `parse_int`, then checks `quantum <= 0` and raises `ValidationError("Time quantum must be greater than 0.")`.
- **Calls:** `parse_int`.
- **Called by:** `api_schedule` (only for `rr`), `api_compare` (always).

### `validate_processes(raw_processes)`

- **Purpose:** Validate and normalise the complete process list.
- **Parameters:** raw JSON value expected to be a list of objects.
- **Returns:** a **new** list of clean dictionaries with exactly `pid`, `arrival`, `burst`, `priority`.
- **Internal working:**
  1. Reject `None`, non-list values, an empty list, or more than `MAX_PROCESSES` (100).
  2. Loop with `enumerate(raw_processes, start=1)`.
  3. Check each item is a dict.
  4. Trim the PID; reject empty IDs, IDs longer than 16 characters or containing anything outside letters/digits/`_`/`-`.
  5. Reject the reserved ID `Idle` (case-insensitive).
  6. Reject duplicate PIDs case-insensitively using a `seen_pids` set.
  7. Parse arrival, burst and priority with `parse_int`.
  8. Enforce arrival ≥ 0, burst > 0 and priority ≥ 0.
  9. Append a clean dictionary.
- **Data structures:** `cleaned` list, `seen_pids` set.
- **Calls:** `parse_int`, `ValidationError`.
- **Called by:** `api_schedule`, `api_compare`.

### `read_request_body()`

- **Purpose:** Read the JSON request body and ensure it is an object.
- **Parameters:** none (uses Flask's `request`).
- **Returns:** `dict`.
- **Internal working:** `request.get_json(silent=True)`; if the result is not a `dict`, raises `ValidationError("Send a JSON object with a 'processes' array.")`.
- **Calls:** `ValidationError`.
- **Called by:** both API routes.

### `index()`

- **Purpose:** Serve the website.
- **Route:** `GET /`
- **Returns:** rendered `templates/index.html`.
- **Calls:** Flask `render_template`.
- **Called by:** the browser.

### `api_schedule()`

- **Purpose:** Run one algorithm and return the complete schedule + metrics.
- **Route:** `POST /api/schedule`
- **Request fields:** `processes` (required), `algorithm` (required: `fcfs`, `sjf`, `srtf`, `rr`, `priority`, `priority_preemptive`), `quantum` (required only for `rr`).
- **Returns:** HTTP 200 JSON schedule, or HTTP 400 `{"error": ...}`.
- **Internal working:**
  1. `read_request_body()`.
  2. `validate_processes(...)`.
  3. Lowercase the algorithm and check it is in `ALLOWED_ALGORITHMS`.
  4. If `rr`, validate the quantum; otherwise pass `None`.
  5. `run_algorithm(...)` → raw schedule.
  6. `calculate_metrics(...)` → final schedule.
  7. `jsonify(...)`.
  8. Catch `ValidationError` and `ValueError` and return `error_response`.
- **Calls:** `read_request_body`, `validate_processes`, `validate_quantum`, `run_algorithm`, `calculate_metrics`, `error_response`.
- **Called by:** `main.js → runSimulation → postJSON`.

### `api_compare()`

- **Purpose:** Run all six algorithms on the same process list and quantum.
- **Route:** `POST /api/compare`
- **Request fields:** `processes`, `quantum` (always required because Round Robin is included).
- **Returns:** HTTP 200 JSON:
  ```json
  {
    "process_count": 5,
    "quantum": 2,
    "results": [
      {"algorithm_key": "fcfs", "algorithm": "FCFS", "quantum": null, "metrics": { ... }},
      {"algorithm_key": "sjf", "algorithm": "SJF", "quantum": null, "metrics": { ... }},
      {"algorithm_key": "srtf", "algorithm": "SRTF", "quantum": null, "metrics": { ... }},
      {"algorithm_key": "rr", "algorithm": "Round Robin", "quantum": 2, "metrics": { ... }},
      {"algorithm_key": "priority", "algorithm": "Priority", "quantum": null, "metrics": { ... }},
      {"algorithm_key": "priority_preemptive", "algorithm": "Preemptive Priority", "quantum": null, "metrics": { ... }}
    ],
    "best": {
      "avg_turnaround_time": ["SRTF"],
      "avg_waiting_time": ["SRTF"],
      "avg_response_time": ["Round Robin"],
      "cpu_utilization": ["FCFS", "SJF", "SRTF", "Round Robin", "Priority", "Preemptive Priority"]
    }
  }
  ```
- **Internal working:** validates once, then loops over `ALLOWED_ALGORITHMS`, runs each algorithm with the shared quantum, calls `calculate_metrics`, keeps only the fields needed for comparison, and calls `find_best_algorithms(results)`.
- **Calls:** `read_request_body`, `validate_processes`, `validate_quantum`, `run_algorithm`, `calculate_metrics`, `find_best_algorithms`, `error_response`.
- **Called by:** `main.js → compareAlgorithms → postJSON`.

### Module-level settings

```python
ALLOWED_ALGORITHMS = (
    "fcfs",
    "sjf",
    "srtf",
    "rr",
    "priority",
    "priority_preemptive",
)
MAX_PROCESSES = 100
PID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,16}$")
```

`app.json.sort_keys = False` keeps JSON key order stable for readable API output.

---

## 3. `scheduler/algorithms.py` — pure scheduling logic

### `pid_sort_key(pid)`

- **Purpose:** Natural ordering for Process IDs.
- **Parameters:** `pid` (string or value convertible to string).
- **Returns:** a tuple usable as a sort key.
- **Internal working:** uses `re.fullmatch(r"(.*?)(\d+)", text)`. If the ID ends in digits, returns `(0, prefix.lower(), int(number))`; otherwise returns `(1, text.lower(), 0)`. The first tuple element keeps numeric IDs before purely textual IDs, and the integer component makes `P2 < P10`.
- **Data structures:** tuple, regular expression.
- **Calls:** none.
- **Called by:** `fcfs`, `_non_preemptive`, `_preemptive`, `round_robin` (through their sort keys).

### `merge_timeline(timeline)`

- **Purpose:** Merge adjacent blocks belonging to the same process, as required for Round Robin, SRTF and Preemptive Priority output.
- **Parameters:** `timeline` list of `{"pid", "start", "end"}` blocks.
- **Returns:** a new merged list; input blocks are not modified.
- **Internal working:** iterates once. If the previous merged block has the same PID **and** `previous["end"] == block["start"]`, it extends the previous block's `end`; otherwise it appends a copy.
- **Data structures:** `merged` list.
- **Calls:** none.
- **Called by:** `_build_result` for every algorithm.

### `_record(process, start, end)`

- **Purpose:** Create one per-process result row with the fields shared by all algorithms.
- **Parameters:** input process dict, CPU start time, completion time.
- **Returns:** dict with `pid`, `arrival`, `burst`, `priority`, `start_time`, `completion_time`.
- **Internal working:** literal dictionary construction.
- **Calls:** none.
- **Called by:** `fcfs`, `_non_preemptive`, `_preemptive`, `round_robin`.

### `_build_result(algorithm_key, processes, records, timeline, quantum=None)`

- **Purpose:** Assemble the common schedule dictionary.
- **Parameters:** algorithm key, the original input list, a `records` map, the raw timeline, optional quantum.
- **Returns:** the raw schedule dictionary described in section 1.3, with the timeline merged and process rows in **input order**.
- **Internal working:** uses `ALGORITHM_LABELS[algorithm_key]` for the display name; builds `processes` as `[records[p["pid"]] for p in processes]`; calls `merge_timeline`.
- **Data structures:** `records` dict, `timeline` list.
- **Calls:** `merge_timeline`.
- **Called by:** `fcfs`, `_non_preemptive`, `_preemptive`, `round_robin`.

### `fcfs(processes)`

- **Purpose:** First Come, First Served (non-preemptive).
- **Parameters:** validated list of process dicts.
- **Returns:** raw schedule.
- **Internal working:**
  1. Sort by `(arrival, pid_sort_key(pid))`.
  2. Start at `time = 0`.
  3. If `time < arrival`, append an `Idle` block and jump to the arrival.
  4. Run the process for its full burst, append a block, and record start/completion.
  5. Build the result.
- **Data structures:** sorted list, `timeline` list, `records` dict.
- **Calls:** `pid_sort_key`, `_record`, `_build_result`.
- **Called by:** `run_algorithm`; used by tests and `app.py` indirectly.

### `_non_preemptive(processes, algorithm_key, key_function)`

- **Purpose:** Shared engine for SJF and Priority Scheduling.
- **Parameters:** processes, algorithm key, and a `key_function(process)`.
- **Returns:** raw schedule.
- **Internal working:**
  1. Copy processes into `pending`.
  2. At each step, build `available = [p for p in pending if p["arrival"] <= time]`.
  3. If no process is available, find the next arrival, append an `Idle` block, jump time, and continue.
  4. Otherwise pick `min(available, key=key_function)`, run it to completion, append a block, record it, and remove it from `pending`.
  5. Repeat until `pending` is empty.
- **Data structures:** `pending` list, `available` list, `timeline`, `records`.
- **Calls:** `_record`, `_build_result`, and the supplied key function (`pid_sort_key` is called inside those lambdas).
- **Called by:** `sjf`, `priority_scheduling`.

### `sjf(processes)`

- **Purpose:** Shortest Job First (non-preemptive).
- **Parameters:** validated processes.
- **Returns:** raw schedule.
- **Internal working:** calls `_non_preemptive` with key `(burst, arrival, pid_sort_key(pid))`.
- **Calls:** `_non_preemptive`.
- **Called by:** `run_algorithm`.

### `_preemptive(processes, algorithm_key, key_function)`

- **Purpose:** Shared engine for SRTF and Preemptive Priority Scheduling.
- **Parameters:** validated processes, algorithm key, and `key_function(process, remaining)`.
- **Returns:** raw schedule.
- **Internal working:**
  1. Sort processes by `(arrival, pid_sort_key(pid))`.
  2. Build `remaining` (PID → burst), `records`, `timeline`, `completed = 0` and `time = 0`.
  3. While some process is incomplete:
     - Build `available` from processes that have arrived and still have work left.
     - If none are available, insert an `Idle` block and jump to the next arrival.
     - Choose the minimum by `key_function(process, remaining)`.
     - Record the process's first start time if this is its first run.
     - Find the next future arrival; run until the process finishes or that arrival occurs, whichever is sooner.
     - Reduce the remaining burst and append a timeline block.
     - When remaining reaches zero, record completion and increment `completed`.
  4. Build the result, which merges adjacent blocks of the same process.
- **Data structures:** `remaining` dict, `records` dict, `timeline` list, `available` list.
- **Calls:** `pid_sort_key`, `_record`, `_build_result`.
- **Called by:** `srtf`, `preemptive_priority`.

### `srtf(processes)`

- **Purpose:** Shortest Remaining Time First (preemptive SJF).
- **Parameters:** validated processes.
- **Returns:** raw schedule.
- **Internal working:** calls `_preemptive` with key `(remaining[pid], arrival, pid_sort_key(pid))`. A new arrival preempts only when its remaining time is strictly smaller.
- **Calls:** `_preemptive`.
- **Called by:** `run_algorithm`; tests call it directly.

### `priority_scheduling(processes)`

- **Purpose:** Non-preemptive Priority Scheduling, lower number = higher priority.
- **Parameters:** validated processes.
- **Returns:** raw schedule.
- **Internal working:** calls `_non_preemptive` with key `(priority, arrival, pid_sort_key(pid))`.
- **Calls:** `_non_preemptive`.
- **Called by:** `run_algorithm`.

### `preemptive_priority(processes)`

- **Purpose:** Preemptive Priority Scheduling, lower number = higher priority.
- **Parameters:** validated processes.
- **Returns:** raw schedule.
- **Internal working:** calls `_preemptive` with key `(priority, arrival, pid_sort_key(pid))`. A new arrival preempts only when its priority number is strictly smaller; equal priority keeps the earlier-arrived process running.
- **Calls:** `_preemptive`.
- **Called by:** `run_algorithm`; tests call it directly.

### `round_robin(processes, quantum)`

- **Purpose:** Preemptive Round Robin with a fixed quantum.
- **Parameters:** validated processes, integer `quantum > 0`.
- **Returns:** raw schedule with `quantum` stored in the result.
- **Internal working:**
  1. Reject a non-integer or non-positive quantum.
  2. Sort arrivals by `(arrival, pid_sort_key(pid))`.
  3. Build `remaining` (PID → burst), an empty `deque` named `ready`, a `records` dict, and `next_arrival_index = 0`.
  4. Define the nested helper `enqueue_arrivals(until_time)`, which appends every not-yet-queued process whose arrival is `<= until_time`, in sorted order.
  5. While some processes are incomplete:
     - Enqueue arrivals up to the current time.
     - If the queue is empty, append an `Idle` block, jump to the next arrival and enqueue it.
     - Pop the left process; record its start time on its first run.
     - Run `min(quantum, remaining[pid])`.
     - Append a timeline block and update the remaining burst.
     - **Enqueue new arrivals at the current time before re-adding the preempted process.**
     - If work remains, append the process to the right of the queue; otherwise record completion.
  6. Build the result, which merges adjacent blocks.
- **Data structures:** `deque` ready queue, `remaining` dict, `records` dict, `timeline` list.
- **Calls:** `pid_sort_key`, `_record`, `_build_result`, nested `enqueue_arrivals`.
- **Called by:** `run_algorithm`; tests call it directly.

Nested helper:

### `round_robin.enqueue_arrivals(until_time)`

- **Purpose:** Move every process that has arrived by `until_time` into the ready queue exactly once.
- **Parameters:** `until_time` (integer).
- **Returns:** none; mutates `ready` and `next_arrival_index` (`nonlocal`).
- **Internal working:** while the next unqueued process arrival is `<= until_time`, append it and advance the index. Because the input was sorted, this preserves arrival/PID order.
- **Calls:** none.
- **Called by:** `round_robin` at the top of the loop and immediately after each time slice.

### `run_algorithm(algorithm_key, processes, quantum=None)`

- **Purpose:** Dispatcher used by Flask and tests.
- **Parameters:** algorithm key (`fcfs`, `sjf`, `srtf`, `rr`, `priority`, `priority_preemptive`), processes, optional quantum.
- **Returns:** raw schedule.
- **Internal working:** lowercases the key and calls `fcfs`, `sjf`, `srtf`, `priority_scheduling`, `preemptive_priority` or `round_robin`. For `rr`, raises `ValueError` if `quantum is None`. Raises `ValueError` for an unknown key.
- **Calls:** `fcfs`, `sjf`, `srtf`, `priority_scheduling`, `preemptive_priority`, `round_robin`.
- **Called by:** `api_schedule`, `api_compare`, tests.

### Module-level constants

- `IDLE_PID = "Idle"` — reserved label.
- `ALGORITHM_LABELS = {"fcfs": "FCFS", "sjf": "SJF", "srtf": "SRTF", "rr": "Round Robin", "priority": "Priority", "priority_preemptive": "Preemptive Priority"}` - display names.

---

## 4. `scheduler/metrics.py` — formulas and comparison winners

### `calculate_metrics(schedule)`

- **Purpose:** Add TAT, WT and RT to every process, then compute averages and CPU utilization.
- **Parameters:** raw schedule from `run_algorithm`.
- **Returns:** a **new** dictionary (the input is not modified) with enriched `processes` and a `metrics` field.
- **Internal working:**
  1. For each process:
     - `turnaround_time = completion_time - arrival`
     - `waiting_time = turnaround_time - burst`
     - `response_time = start_time - arrival`
  2. Average each value over `process_count` (zero if empty).
  3. `total_time = timeline[-1]["end"]` (timeline starts at 0).
  4. `busy_time = sum(end - start for non-Idle blocks)`.
  5. `idle_time = total_time - busy_time`.
  6. `cpu_utilization = busy_time / total_time * 100` (guard against zero).
- **Data structures:** `rows` list, `metrics` dict.
- **Calls:** none.
- **Called by:** `api_schedule`, `api_compare`, tests.

### `find_best_algorithms(results)`

- **Purpose:** Identify the winner(s) for each comparison metric.
- **Parameters:** list of items containing `"algorithm"` and `"metrics"`.
- **Returns:** dict mapping each metric to a list of algorithm display names.
- **Internal working:** for TAT, WT and RT it takes the minimum; for CPU utilization it takes the maximum. It then collects every result within `1e-9` of the target, preserving ties. A small tolerance prevents floating-point noise from splitting equal values.
- **Data structures:** list of metric definitions, output dict.
- **Calls:** built-in `min` / `max`.
- **Called by:** `api_compare`; tests.

---

## 5. `static/js/main.js` — UI controller

All functions are inside an IIFE, so the global namespace only receives DOM events, not these helpers. The module starts by reading elements into the `elements` object and defining `state`.

### `escapeHtml(value)`

- **Purpose:** Escape user-controlled text before inserting it into `innerHTML`.
- **Parameters:** any value.
- **Returns:** string with `& < > " '` replaced by entities.
- **Calls:** none.
- **Called by:** `renderProcessTable`, `renderResults`, `renderComparison`.

### `formatNumber(value, digits)`

- **Purpose:** Format a number to fixed decimals.
- **Parameters:** `value`, optional digits (default 2).
- **Returns:** fixed string, or `—` when the value is not a finite number.
- **Called by:** `renderResults`, `metricCell`, `renderComparison`.

### `formatCell(value)`

- **Purpose:** Show whole numbers without decimals in the per-process table; decimals otherwise.
- **Parameters:** numeric value.
- **Returns:** string.
- **Calls:** `formatNumber`.
- **Called by:** `renderResults`.

### `showError(element, message)` / `hideError(element)`

- **Purpose:** Show or hide an inline error box.
- **Parameters:** target element, message.
- **Returns:** none.
- **Internal working:** sets `textContent` and the `hidden` property. Because `textContent` is used, messages cannot inject HTML.
- **Called by:** all form, run and comparison handlers.

### `showNotice(message)` / `hideNotice()`

- **Purpose:** Show or hide the green process-list status message.
- **Parameters:** message for `showNotice`.
- **Returns:** none.
- **Called by:** `handleFormSubmit`, `startEdit`, `handleTableClick`, `loadSample`, `clearAllProcesses`, `runSimulation`, `compareAlgorithms`.

### `setButtonBusy(button, isBusy, idleText, busyText)`

- **Purpose:** Prevent double submission and show progress text.
- **Parameters:** button element, busy flag, normal label, busy label.
- **Returns:** none.
- **Internal working:** sets `disabled`, `textContent` and `aria-busy`.
- **Called by:** `runSimulation`, `compareAlgorithms`.

### `scrollToElement(element)`

- **Purpose:** Smoothly scroll a section into view.
- **Parameters:** element.
- **Returns:** none.
- **Internal working:** uses `scrollIntoView`; uses `auto` instead of `smooth` when the user prefers reduced motion.
- **Called by:** `loadSample`, `runSimulation`, `compareAlgorithms`.

### `currentTheme()`

- **Purpose:** Return `"dark"` or `"light"` from the document's `data-theme` attribute.
- **Returns:** string.
- **Called by:** `applyTheme`, `setupTheme`.

### `applyTheme(theme, persist)`

- **Purpose:** Apply a theme, update the toggle's accessible label, update the browser theme colour, and optionally save the choice.
- **Parameters:** `"dark"`/`"light"`, and a boolean that controls `localStorage` persistence.
- **Returns:** none.
- **Internal working:** sets `data-theme` on `<html>`, updates `aria-pressed`, `aria-label`, `title` and `#theme-color-meta`, stores `cpu-scheduler-theme` when requested, and redraws an open Chart.js comparison using `ComparisonCharts.render`.
- **Called by:** `setupTheme` and the theme toggle click handler.

### `setupTheme()`

- **Purpose:** Initialise the saved or system theme and wire the header toggle.
- **Returns:** none.
- **Internal working:** reads `cpu-scheduler-theme` (silently falls back if storage is blocked), applies it without re-saving, then registers the click handler that toggles and persists the new theme.
- **Called by:** initial startup.

### `readIntegerField(input, label, minimum, rangeMessage)`

- **Purpose:** Client-side whole-number parsing and range validation.
- **Parameters:** input element, field label, minimum, message when below minimum.
- **Returns:** integer.
- **Internal working:** trims; rejects empty and non-matching `^[+-]?\d+$`; uses `Number.isSafeInteger`; checks the minimum and throws an `Error` with a user-friendly message.
- **Called by:** `readProcessForm`, `readQuantum`.

### `renderProcessTable()`

- **Purpose:** Redraw the editable process table and count badge.
- **Parameters:** none (reads `state.processes`).
- **Returns:** none.
- **Internal working:** for zero rows, writes one `colspan="5"` empty-state row. Otherwise maps each process to a `<tr>` with a PID chip, arrival, burst, priority, and Edit/Delete buttons carrying `data-action` and `data-index`. All PIDs are escaped.
- **Data structures:** `state.processes`.
- **Calls:** `escapeHtml`.
- **Called by:** `handleFormSubmit`, `handleTableClick`, `loadSample`, `clearAllProcesses`, and initial startup.

### `readProcessForm()`

- **Purpose:** Read and validate the four input fields.
- **Parameters:** none.
- **Returns:** `{pid, arrival, burst, priority}`.
- **Internal working:** trims the PID; checks non-empty, the 1-16 character pattern and the reserved `Idle`; calls `readIntegerField` for arrival (min 0), burst (min 1) and priority (min 0).
- **Calls:** `readIntegerField`, `Error`.
- **Called by:** `handleFormSubmit`.

### `resetForm()`

- **Purpose:** Return the form to add mode.
- **Parameters:** none.
- **Returns:** none.
- **Internal working:** clears `editIndex`, calls `form.reset()`, resets button text and hint, hides Cancel and the error box.
- **Called by:** `handleFormSubmit`, `handleTableClick`, `loadSample`, `clearAllProcesses`, Cancel button handler.

### `handleFormSubmit(event)`

- **Purpose:** Add a new process or save an edited one.
- **Parameters:** submit event.
- **Returns:** none.
- **Internal working:**
  1. Prevent the default form submission.
  2. Clear old messages.
  3. Read the form and check for a duplicate PID, ignoring the row currently being edited (case-insensitive).
  4. Push or replace the process.
  5. Show a notice, reset the form, redraw the table, invalidate old results, and focus the PID field.
  6. Catch validation errors and show them in `#form-error`.
- **Calls:** `readProcessForm`, `showNotice`, `showError`, `hideError`, `hideNotice`, `resetForm`, `renderProcessTable`, `invalidateResults`.
- **Called by:** form `submit` event.

### `startEdit(index)`

- **Purpose:** Load one process into the form for editing.
- **Parameters:** list index.
- **Returns:** none.
- **Internal working:** stores `editIndex`, fills the four inputs, changes the submit button to **Update process**, reveals **Cancel edit**, updates the hint, and focuses/selects the PID input.
- **Calls:** `showError`, `hideNotice`.
- **Called by:** `handleTableClick` when an Edit button is clicked.

### `handleTableClick(event)`

- **Purpose:** Event delegation for Edit and Delete buttons.
- **Parameters:** click event.
- **Returns:** none.
- **Internal working:** finds the nearest `button[data-action]`, validates the row index, calls `startEdit` for Edit. For Delete it splices the process out, adjusts `editIndex` (reset if the edited row was deleted, decrement if an earlier row was deleted), redraws, invalidates results and shows a notice.
- **Calls:** `startEdit`, `resetForm`, `renderProcessTable`, `invalidateResults`, `showNotice`.
- **Called by:** click listener on `#process-tbody`.

### `loadSample()`

- **Purpose:** Replace the list with the five-process sample.
- **Parameters:** none.
- **Returns:** none.
- **Internal working:** deep-copies `SAMPLE_PROCESSES`, resets the form, redraws, invalidates results, shows a notice and scrolls to the process section.
- **Calls:** `resetForm`, `renderProcessTable`, `invalidateResults`, `showNotice`, `scrollToElement`.
- **Called by:** **Load sample** buttons in the hero and process section.

### `clearAllProcesses()`

- **Purpose:** Empty the process list.
- **Parameters:** none.
- **Returns:** none.
- **Internal working:** if already empty, shows a notice. Otherwise clears the array, resets the form, redraws, invalidates results and confirms the clear.
- **Calls:** `resetForm`, `renderProcessTable`, `invalidateResults`, `showNotice`.
- **Called by:** **Clear all** button.

### `selectAlgorithm(algorithmKey)`

- **Purpose:** Update the selected algorithm card and quantum visibility.
- **Parameters:** `"fcfs" | "sjf" | "srtf" | "rr" | "priority" | "priority_preemptive"`.
- **Returns:** none.
- **Internal working:** stores the selection, toggles the `selected` class on cards, reveals the quantum field only for `rr`, and invalidates old results.
- **Calls:** `invalidateResults`.
- **Called by:** radio `change` listeners and startup.

### `readQuantum()`

- **Purpose:** Read the quantum with client-side validation.
- **Parameters:** none.
- **Returns:** integer > 0.
- **Internal working:** delegates to `readIntegerField` with a Round Robin-specific message.
- **Calls:** `readIntegerField`.
- **Called by:** `runSimulation`, `compareAlgorithms`.

### `invalidateResults()`

- **Purpose:** Remove stale results after the process list, algorithm or quantum changes.
- **Parameters:** none.
- **Returns:** none.
- **Internal working:** clears `lastResult` and `lastComparison`, shows both empty states, hides both result contents and the badge, and clears run/compare errors.
- **Called by:** `selectAlgorithm`, quantum `input` listener, `handleFormSubmit`, `handleTableClick`, `loadSample`, `clearAllProcesses`.

### `renderResults(data)`

- **Purpose:** Display one API schedule.
- **Parameters:** `/api/schedule` JSON.
- **Returns:** none.
- **Internal working:** fills the algorithm badge, four metric cards, busy/idle/total note, Gantt total, subtitle, calls `window.GanttChart.render(...)`, builds the per-process table with `formatCell`, then reveals the results section.
- **Data structures:** response `processes`, `timeline`, `metrics`.
- **Calls:** `formatNumber`, `formatCell`, `escapeHtml`, `GanttChart.render`.
- **Called by:** `runSimulation`.

### `postJSON(url, payload)`

- **Purpose:** POST JSON and normalise error handling.
- **Parameters:** endpoint URL, JS object.
- **Returns:** parsed response object (async/Promise).
- **Internal working:** `fetch` with `Content-Type: application/json`; network failure → friendly "Cannot reach the Flask server" error; parses JSON defensively; non-OK status → server `error` field; missing body → generic error.
- **Calls:** browser `fetch`.
- **Called by:** `runSimulation`, `compareAlgorithms`.

### `runSimulation()`

- **Purpose:** Run the selected algorithm and display the result.
- **Parameters:** none.
- **Returns:** none (async).
- **Internal working:** rejects an empty list, validates the quantum when needed, disables the button, posts to `/api/schedule`, stores and renders the response, scrolls to results, restores the button, and shows any error inline.
- **Calls:** `hideError`, `hideNotice`, `showError`, `readQuantum`, `setButtonBusy`, `postJSON`, `renderResults`, `scrollToElement`.
- **Called by:** **Run simulation** button.

### `metricCell(result, metricKey, suffix, best)`

- **Purpose:** Build one comparison table cell.
- **Parameters:** result object, metric key, suffix (`%` or empty), best map.
- **Returns:** HTML string for a `<td>`.
- **Internal working:** checks whether the algorithm is in `best[metricKey]`, adds `class="best"` and a title when it is, and formats the value to two decimals.
- **Calls:** `formatNumber`.
- **Called by:** `renderComparison`.

### `renderComparison(data)`

- **Purpose:** Display the comparison callouts, table and charts.
- **Parameters:** `/api/compare` JSON.
- **Returns:** none.
- **Internal working:**
  1. Sets the badge to process count and quantum.
  2. Builds four best-value cards.
  3. Builds one table row per algorithm, using `metricCell`.
  4. Reveals the comparison section **before** calling Chart.js so the canvases have a measurable size.
  5. Calls `window.ComparisonCharts.render`.
- **Calls:** `escapeHtml`, `formatNumber`, `metricCell`, `ComparisonCharts.render`.
- **Called by:** `compareAlgorithms`.

### `compareAlgorithms()`

- **Purpose:** Run all six algorithms and show the comparison.
- **Parameters:** none.
- **Returns:** none (async).
- **Internal working:** rejects an empty list, validates the quantum (with a note that comparison includes Round Robin), disables the button, posts to `/api/compare`, stores and renders the result, scrolls to the section, restores the button and shows inline errors.
- **Calls:** `showError`, `hideNotice`, `readQuantum`, `setButtonBusy`, `postJSON`, `renderComparison`, `scrollToElement`.
- **Called by:** **Compare all six** button.

### `setupScrollSpy()`

- **Purpose:** Highlight the nav link for the section currently in view.
- **Parameters:** none.
- **Returns:** none.
- **Internal working:** collects nav links and their target sections, then uses an `IntersectionObserver` with a middle-of-viewport root margin to toggle the `active` class. Falls back silently if the browser lacks `IntersectionObserver`.
- **Called by:** startup only.

### Startup and event wiring

At the bottom of the IIFE, listeners are attached for the form submit, Cancel button, table clicks, sample/clear buttons, algorithm radios, quantum input, theme toggle, and run/compare buttons. Startup calls `renderProcessTable()`, `setupTheme()`, `selectAlgorithm("fcfs")` and `setupScrollSpy()`.

---

## 6. `static/js/gantt.js` — custom chart renderer

### `escapeHtml(value)`

- **Purpose:** Local copy of the HTML escaper for PID labels.
- **Called by:** `showTooltip`, `render`.

### `buildColorMap(timeline)`

- **Purpose:** Assign a stable colour to each process.
- **Parameters:** timeline blocks.
- **Returns:** object mapping PID → palette colour.
- **Internal working:** collects unique non-idle PIDs, sorts them with `localeCompare(..., {numeric: true})`, and assigns colours from a 10-colour palette in order. Sorting makes the colours stable when the user switches algorithms.
- **Called by:** `render`.

### `getTooltip()`

- **Purpose:** Lazily create the single shared tooltip element.
- **Returns:** tooltip DOM element.
- **Internal working:** creates a `div.gantt-tooltip`, sets `role="tooltip"`, hides it, and appends it to `document.body`.
- **Called by:** `showTooltip`, `positionTooltip`.

### `hideTooltip()`

- **Purpose:** Hide the shared tooltip.
- **Called by:** block `mouseleave` / `blur`, page scroll (capture) and window resize.

### `positionTooltip(x, y)`

- **Purpose:** Place the tooltip near the pointer without leaving the viewport.
- **Parameters:** client coordinates.
- **Internal working:** starts 14 px to the bottom-right; flips left/up when it would overflow; clamps to at least 8 px.
- **Calls:** `getTooltip`.
- **Called by:** `showTooltip`, block `mousemove`.

### `showTooltip(block, x, y)`

- **Purpose:** Fill and display the tooltip for one block.
- **Parameters:** timeline block, x, y.
- **Internal working:** shows PID (or “CPU idle”), start, end and duration. Uses `escapeHtml`.
- **Calls:** `getTooltip`, `escapeHtml`, `positionTooltip`.
- **Called by:** block `mouseenter` and `focus` listeners.

### `createLegendItem(pid, color, isIdle)`

- **Purpose:** Build one legend chip.
- **Parameters:** label, colour or `null`, idle flag.
- **Returns:** DOM element.
- **Called by:** `renderLegend`.

### `renderLegend(legendContainer, timeline, colors)`

- **Purpose:** Draw the process colour legend.
- **Parameters:** target container, timeline, colour map.
- **Internal working:** one chip per process plus an idle chip when the timeline contains `Idle`.
- **Calls:** `createLegendItem`.
- **Called by:** `render`.

### `render(timeline, container, legendContainer)`

- **Purpose:** Render the complete Gantt chart.
- **Parameters:** timeline blocks, chart container, legend container.
- **Returns:** none.
- **Internal working:**
  1. Clear old content and show a message if the timeline is empty.
  2. Build the colour map.
  3. Create `.gantt-scroll` → `.gantt-track`.
  4. For each block create `.gantt-block`; set `flexGrow` to the duration so widths follow the duration; set a background colour (except idle); add PID and start–end labels with `textContent`; make it focusable; attach mouse/focus listeners.
  5. Build a matching `.gantt-axis` row whose segments use the same `flexGrow`, so labels align with block boundaries.
  6. Append the track and axis, then render the legend.
- **Data structures:** DOM elements; `colors` object.
- **Calls (at render time):** `buildColorMap`, `renderLegend`. The listeners it attaches call `showTooltip`, `positionTooltip` and `hideTooltip` later.
- **Called by:** `main.js → renderResults` through `window.GanttChart.render`.

The module exports `window.GanttChart = { render: render }`.

---

## 7. `static/js/charts.js` - Chart.js comparison charts

### `palette()`

- **Purpose:** Return theme-aware chart colours for bars, borders, ticks, grid lines and tooltips.
- **Returns:** object of colour strings, selected from `data-theme`.
- **Called by:** `makeChart`.

### `isBest(bestList, algorithmName)`

- **Purpose:** Check whether an algorithm is a winner for one metric.
- **Parameters:** best list from the API, algorithm display name.
- **Returns:** boolean.
- **Called by:** `makeChart`.

### `showFallback()`

- **Purpose:** Replace chart canvases with a readable message when Chart.js is unavailable.
- **Parameters:** none.
- **Internal working:** finds every `.chart-box`, replaces its contents with a `.chart-fallback` paragraph explaining that the table still works.
- **Called by:** `render` when `Chart` is undefined.

### `destroyCharts()`

- **Purpose:** Destroy existing Chart.js instances before re-rendering.
- **Parameters:** none.
- **Internal working:** calls `.destroy()` on every stored chart and resets the `charts` object. This prevents "Canvas is already in use" errors.
- **Called by:** `render`.

### `makeChart(canvasId, key, labels, values, bestList, algorithms, metricLabel, suffix)`

- **Purpose:** Create one bar chart.
- **Parameters:** canvas ID, storage key, x labels, values, best map, algorithm names, metric label, suffix.
- **Returns:** none; stores the chart in `charts[key]`.
- **Internal working:** computes green colours for winners and teal for the rest, then creates a Chart.js bar chart with animations disabled, no legend, value tooltips, a zero-based y-axis and rounded bars.
- **Calls:** `isBest`, `new Chart`.
- **Called by:** `render`.

### `render(results, best)`

- **Purpose:** Draw all three comparison charts.
- **Parameters:** `/api/compare` results and best map.
- **Returns:** none.
- **Internal working:** shows the fallback if Chart.js failed; destroys old charts; builds compact labels (`FCFS`, `SJF`, `SRTF`, `RR (q=n)`, `Priority`, `Prem. Priority`); calls `makeChart` for waiting, turnaround and response time.
- **Calls:** `showFallback`, `destroyCharts`, `makeChart`.
- **Called by:** `main.js → renderComparison` through `window.ComparisonCharts.render`.

The module exports `window.ComparisonCharts = { render: render }`.

---

## 8. Function call summary

```text
Browser submit
└── handleFormSubmit
    ├── readProcessForm → readIntegerField
    ├── renderProcessTable → escapeHtml
    └── invalidateResults

Run simulation
└── runSimulation
    ├── readQuantum → readIntegerField
    ├── postJSON → fetch
    └── renderResults
        ├── formatNumber / formatCell / escapeHtml
        └── GanttChart.render → buildColorMap / renderLegend

Compare all six
└── compareAlgorithms
    ├── readQuantum
    ├── postJSON
    └── renderComparison
        ├── metricCell → formatNumber
        └── ComparisonCharts.render → makeChart / destroyCharts

Flask /api/schedule
└── api_schedule
    ├── read_request_body
    ├── validate_processes → parse_int
    ├── validate_quantum → parse_int
    ├── run_algorithm
    │   ├── fcfs
    │   ├── sjf → _non_preemptive
    │   ├── srtf
    │   │   └── _preemptive
    │   ├── priority_scheduling → _non_preemptive
    │   ├── preemptive_priority
    │   │   └── _preemptive
    │   └── round_robin → enqueue_arrivals
    │       └── _build_result → merge_timeline
    └── calculate_metrics
```
