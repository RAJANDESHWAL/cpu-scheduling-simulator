# CPU Scheduler Lab

A complete, browser-based **CPU Task Scheduler Simulator** built as an Operating Systems mini-project. It runs four classic single-core scheduling algorithms on a process list that you build in the page, then shows a Gantt chart, per-process metrics, averages and an algorithm comparison with Chart.js bar charts.

> **Simulation only:** this project demonstrates how CPU scheduling algorithms behave. It does **not** read, control or modify the real scheduler of your operating system.

---

## Overview

Operating systems must decide which ready process gets the CPU next. Different policies produce different waiting times, turnaround times and response times. This simulator makes those differences visible:

1. Add processes with an arrival time, burst time and priority.
2. Choose FCFS, SJF, Round Robin or Priority Scheduling.
3. Run the simulation and inspect the Gantt chart and metrics.
4. Compare all four algorithms on exactly the same input.

The application is served locally by **Flask** and runs entirely in a web browser. There is no Tkinter window, desktop GUI or external database.

---

## Objectives

- Implement four standard CPU scheduling algorithms from scratch in pure Python.
- Apply one consistent set of scheduling and tie-breaking rules.
- Calculate CT, TAT, WT, RT and CPU utilization correctly.
- Visualise the schedule as an interactive Gantt chart.
- Let a user add, edit and delete processes without reloading the page.
- Compare all four algorithms on identical inputs and identify the best result per metric.
- Keep scheduling logic separate from Flask and from frontend code so that every part is easy to test and explain.

---

## Features

- **Process management:** add, edit and delete processes; duplicate-ID detection; reserved `Idle` label.
- **Four algorithms:** FCFS, SJF, Round Robin (configurable quantum) and non-preemptive Priority Scheduling.
- **Interactive Gantt chart:** duration-scaled coloured blocks with a readable minimum width, process labels, time markers, hover/focus tooltips, idle blocks and a legend.
- **Per-process results:** arrival, burst, priority, first start, completion, TAT, WT and RT.
- **Summary metrics:** average TAT, average WT, average RT, CPU utilization, busy time, idle time and total elapsed time.
- **Comparison:** side-by-side table, best algorithm per metric, three Chart.js bar charts, and tie highlighting.
- **One-click sample workload** and **clear-all**.
- **Inline validation** on the page (no browser `alert()` popups).
- **Responsive layout** for desktop, tablet and mobile.
- **45 automated Python tests** covering algorithms, metrics, edge cases and API validation.

---

## Algorithms

| Key | Algorithm | Preemptive? | Selection rule |
|---|---|---|---|
| `fcfs` | First Come, First Served | No | Process with the earliest arrival time runs to completion. |
| `sjf` | Shortest Job First | No | Among arrived processes, the smallest burst time runs to completion. |
| `rr` | Round Robin | Yes | Each process runs for at most one time quantum, then re-joins the ready queue. |
| `priority` | Priority Scheduling | No | Among arrived processes, the smallest priority number runs to completion. |

### Scheduling conventions used everywhere

- **Tie-breaking:** compare arrival time, then burst time or priority as appropriate, and finally the smaller Process ID.
- **Simultaneous arrivals:** all processes arriving at the same time become available together and are ordered by the tie-breaking rule.
- **Process ID ordering:** natural ordering is used, so `P2` comes before `P10`. IDs without a numeric suffix are compared case-insensitively.
- **Idle CPU:** if no process has arrived, an `Idle` block is inserted and time jumps to the next arrival. Idle time is excluded from CPU utilization.
- **Round Robin queue rule:** a process that arrives exactly when another process's quantum expires enters the ready queue **before** the preempted process is added back.
- **Round Robin Gantt rule:** consecutive blocks belonging to the same process are merged (for example `0-2, 2-4, 4-5` becomes `0-5`).
- **Response time:** first CPU start time minus arrival time.
- **Formulas:**
  - `TAT = CT - AT`
  - `WT = TAT - BT`
  - `RT = first start - AT`
  - `CPU utilization = (busy time / total elapsed time) × 100`
- **Total elapsed time:** measured from time `0` to the last completion, so initial idle time is included in the denominator.
- **No overhead:** context-switch time, dispatcher time and I/O are ignored.

---

## Technology stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Flask 3 |
| Scheduling engine | Pure Python (`scheduler/`), no Flask imports |
| Frontend | HTML, CSS, vanilla JavaScript |
| Gantt chart | Custom HTML/CSS/JavaScript renderer |
| Comparison charts | Chart.js 4 loaded from the jsDelivr CDN |
| Tests | pytest + Flask test client |
| Editor | Visual Studio Code on Windows |

---

## Project structure

```
cpu-scheduler-simulator/
├── .gitignore                  Ignores caches and virtual environments
├── app.py                      Flask routes, request validation, JSON API
├── requirements.txt            Python dependencies
├── scheduler/
│   ├── __init__.py             Package marker and short description
│   ├── algorithms.py           FCFS, SJF, Round Robin, Priority (pure Python)
│   └── metrics.py              CT/TAT/WT/RT, averages, utilisation, best-algorithm helper
├── templates/
│   └── index.html              The single-page website
├── static/
│   ├── css/
│   │   └── style.css           Layout, theme and responsive styles
│   ├── js/
│   │   ├── main.js             Process CRUD, validation, API calls, result rendering
│   │   ├── gantt.js            Custom Gantt renderer, tooltips and legend
│   │   └── charts.js           Chart.js comparison bar charts
│   └── favicon.svg             Browser tab icon
├── tests/
│   └── test_algorithms.py      Algorithm, metric and API tests
└── docs/
    ├── README.md               This file
    ├── FUNCTION_GUIDE.md       Function-by-function reference
    ├── CODE_WALKTHROUGH.md     Execution flow, API examples, call hierarchy, flowcharts
    ├── VIVA_PREPARATION.md     78 viva questions and answers
    └── TEST_CASES.md           Hand-verified test cases and expected outputs
```

### Why this structure?

- **`scheduler/algorithms.py`** contains only scheduling logic. It can be imported and tested without Flask, a browser or a server.
- **`scheduler/metrics.py`** keeps every formula in one place, so all four algorithms are measured identically.
- **`app.py`** is a thin HTTP layer: it validates JSON, calls the scheduler, and returns JSON.
- **`main.js`** owns UI state and talks to the API. **`gantt.js`** and **`charts.js`** each render one kind of visual.
- **`index.html`** is a single page with sections and smooth-scroll navigation. This keeps the frontend easy to demonstrate and avoids a build step.

---

## How the parts interact

```
Browser (index.html + main.js)
        |
        |  fetch POST /api/schedule or /api/compare  (JSON)
        v
Flask app.py
        |
        |  validate_processes() -> run_algorithm() -> calculate_metrics()
        v
scheduler/algorithms.py  +  scheduler/metrics.py
        |
        |  JSON response: timeline, process rows, metrics
        v
main.js -> gantt.js (Gantt chart)
        -> charts.js (comparison bar charts)
```

Each request is independent and stateless. The browser keeps the process list and sends the full list with every request; there is no database or server-side session.

---

## API endpoints

### `POST /api/schedule`

Runs one algorithm.

```json
{
  "processes": [
    { "pid": "P1", "arrival": 0, "burst": 3, "priority": 1 },
    { "pid": "P2", "arrival": 2, "burst": 1, "priority": 2 }
  ],
  "algorithm": "fcfs",
  "quantum": null
}
```

`quantum` is required only when `algorithm` is `"rr"`. Successful responses contain `algorithm_key`, `algorithm`, `quantum`, `timeline`, `processes` and `metrics`. Invalid input returns HTTP 400 with `{"error": "..."}`.

### `POST /api/compare`

Runs all four algorithms on the same list. `quantum` is always required because Round Robin is included.

```json
{
  "processes": [
    { "pid": "P1", "arrival": 0, "burst": 3, "priority": 1 }
  ],
  "quantum": 2
}
```

The response contains each algorithm's metrics and a `best` object listing the winning algorithm(s) for average TAT, average WT, average RT and CPU utilization.

### `GET /`

Serves the single-page website.

Detailed request/response examples and call flows are in [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md).

---

## Installation and running on Windows

### Prerequisites

- Python 3.10 or newer (tested with Python 3.13.9)
- A modern browser (Chrome, Edge, Firefox)
- Internet access for the Chart.js CDN when viewing the comparison charts
- Visual Studio Code (recommended, not required)

### Steps

Open a terminal in the project folder:

```powershell
cd cpu-scheduler-simulator
```

Optional but recommended virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Start the Flask server:

```powershell
python app.py
```

Open this URL in the browser:

```text
http://127.0.0.1:5000
```

Press `Ctrl+C` in the terminal to stop the server.

### Visual Studio Code

1. Open the `cpu-scheduler-simulator` folder in VS Code.
2. Open **Terminal → New Terminal**.
3. Run the commands above.
4. Open `http://127.0.0.1:5000` in a browser (or `Ctrl+Click` the URL printed by Flask).

The page loads Chart.js from `https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js`. If the CDN is unreachable, the comparison table still works and the chart areas show an explanatory fallback message.

---

## Using the website

1. **Load a workload.** Press **Load sample** for five ready-made processes, or add your own.
2. **Add a process.** Enter a Process ID, whole-number arrival time, burst time and priority. Press **Add process**.
3. **Edit or delete.** Use the **Edit** and **Delete** buttons in the process table. Editing keeps the process in its current list position; **Cancel edit** restores add mode.
4. **Choose an algorithm.** Click one of the four algorithm cards. The quantum field appears only for Round Robin.
5. **Run.** Press **Run simulation**. The page shows the Gantt chart, per-process metrics and averages.
6. **Compare.** Press **Compare all four** to run every algorithm on the same list. The best value in each metric is highlighted.
7. **Start over.** Press **Clear all** to empty the process list.

Validation errors appear next to the form or the relevant action button. The browser never uses `alert()`.

---

## Running the automated tests

From the project folder:

```powershell
python -m pytest -v
```

Actual final result from this build:

```text
45 passed in 0.30s
```

Exact timing varies slightly between machines and runs.

The tests cover:

- FCFS, SJF, Priority and Round Robin on a shared sample
- Round Robin's arrival-at-expiry ordering rule
- quantum of 1, quantum larger than every burst, invalid quantum
- idle gaps and CPU utilization
- single process with initial idle time
- equal-burst, equal-priority and simultaneous-arrival tie-breaking
- merged Round Robin Gantt blocks
- `find_best_algorithms` with and without ties
- all API success paths and validation failures
- static assets and the index page

The hand calculations for these values are in [TEST_CASES.md](TEST_CASES.md).

---

## Screenshots

> **No screenshot image files are included in this project.** The entries below are deliberate placeholders for you to replace with your own screenshots during the demonstration or report. Create a `docs/images/` folder and save your images there.

### 1. Home / dashboard

- **Placeholder:** `[INSERT HOME PAGE SCREENSHOT HERE]`
- **Suggested file:** `docs/images/01-home.png`
- **Capture:** the hero section with the project title, introduction, disclaimer and example timeline card.

### 2. Process management

- **Placeholder:** `[INSERT PROCESS MANAGEMENT SCREENSHOT HERE]`
- **Suggested file:** `docs/images/02-processes.png`
- **Capture:** the add-process form and a populated process table with Edit/Delete buttons.

### 3. Algorithm selection

- **Placeholder:** `[INSERT ALGORITHM SELECTION SCREENSHOT HERE]`
- **Suggested file:** `docs/images/03-algorithm.png`
- **Capture:** all four algorithm cards with Round Robin selected so the quantum field is visible.

### 4. Simulation results

- **Placeholder:** `[INSERT RESULTS AND GANTT CHART SCREENSHOT HERE]`
- **Suggested file:** `docs/images/04-results.png`
- **Capture:** the four metric cards, the Gantt chart with its legend, and the per-process metrics table.

### 5. Algorithm comparison

- **Placeholder:** `[INSERT COMPARISON SCREENSHOT HERE]`
- **Suggested file:** `docs/images/05-comparison.png`
- **Capture:** the best-per-metric callouts, the comparison table with highlighted winners, and all three bar charts.

---

## Limitations and notes

- **Simulation, not control:** the program never interacts with the real OS scheduler.
- **Single core only:** no multiprocessor load balancing.
- **Whole-number time units:** arrival, burst, priority and quantum must be integers. Decimal times are rejected.
- **No I/O or context-switch overhead:** processes are CPU-bound and switching is free.
- **Priority is non-preemptive** in this project, as required by the brief.
- **No aging:** SJF and Priority can starve long or low-priority processes in theory.
- **In-memory only:** processes are stored in browser memory; refreshing the page clears them.
- **Maximum 100 processes** per request.
- **Chart.js is external:** comparison charts need network access to the CDN; tables do not.
- **Process IDs** are 1-16 letters, numbers, hyphens or underscores. `Idle` is reserved for the Gantt chart.

---

## Documentation map

| Document | Contents |
|---|---|
| [README.md](README.md) | Overview, setup, features, screenshots placeholders |
| [FUNCTION_GUIDE.md](FUNCTION_GUIDE.md) | Every important Python and JavaScript function |
| [CODE_WALKTHROUGH.md](CODE_WALKTHROUGH.md) | End-to-end flow, API examples, call hierarchy, Mermaid flowcharts |
| [VIVA_PREPARATION.md](VIVA_PREPARATION.md) | 78 questions with simple, technically correct answers |
| [TEST_CASES.md](TEST_CASES.md) | Hand-verified inputs, outputs, Gantt charts and validation cases |
