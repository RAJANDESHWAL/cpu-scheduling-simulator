# Viva Preparation — 85 Questions and Answers

Answers are intentionally short and technically correct. Project-specific statements refer to the actual implementation in this repository.

---

## A. Operating-system fundamentals

### 1. What is an operating system?

An operating system is system software that manages hardware resources (CPU, memory, I/O devices) and provides services to application programs. It acts as an intermediary between the user and the hardware.

### 2. What is a process?

A process is a program in execution. It includes the program code, current activity (program counter, registers), a stack, a data section, and OS bookkeeping information. A program on disk is passive; a process is active.

### 3. What is the difference between a program and a process?

A program is a static file of instructions. A process is an executing instance of that program with its own state and resources. The same program can create several processes.

### 4. What are the basic states of a process?

New, ready, running, waiting/blocked, and terminated. This simulator deals mainly with **ready**, **running** and **terminated** because processes are CPU-bound and do not perform I/O.

### 5. What is a Process Control Block (PCB)?

A PCB is the data structure the OS uses to track a process. It typically stores the PID, process state, program counter, CPU registers, memory limits, priority and accounting information. This project stores a simplified process record instead of a real PCB.

### 6. What is a scheduler?

A scheduler is the OS component that chooses which process should use the CPU or be admitted into the system. Long-term scheduling admits jobs, short-term scheduling selects the next process for the CPU, and medium-term scheduling handles swapping. This project models **short-term CPU scheduling**.

### 7. What is the dispatcher?

The dispatcher is the component that actually gives the CPU to the process selected by the scheduler. It performs context switching, switching to user mode, and jumping to the correct program location.

### 8. What is dispatch latency?

Dispatch latency is the time taken by the dispatcher to stop one process and start another. This simulator ignores dispatch latency, so switching costs zero time.

### 9. What is a context switch?

A context switch is the act of saving the state of the current process and restoring the state of another so it can run. It takes time in a real OS. This project does not model context-switch overhead.

### 10. What is the difference between preemptive and non-preemptive scheduling?

In non-preemptive scheduling, a running process keeps the CPU until it finishes or blocks. In preemptive scheduling, the OS can interrupt a running process, for example when its time quantum expires or a higher-priority process arrives.

### 11. What is a time quantum?

A time quantum (or time slice) is the maximum continuous CPU time a process receives in Round Robin before it is preempted and moved to the back of the ready queue.

### 12. What is a ready queue?

The ready queue is the collection of processes that are in memory, ready to run, and waiting for the CPU. In this project it is a `collections.deque` in `round_robin()`.

### 13. What is a CPU burst?

A CPU burst is a period during which a process executes continuously on the CPU without waiting for I/O. This simulator assumes every process has one CPU burst equal to its burst time.

---

## B. Scheduling algorithms

### 14. How does FCFS work?

First Come, First Served runs processes in order of arrival. Once a process starts, it runs to completion. If two processes arrive together, the smaller Process ID runs first in this project.

### 15. What are the advantages of FCFS?

It is simple, easy to implement, fair in the sense that no process is skipped indefinitely, and it has low scheduling overhead. It is non-preemptive.

### 16. What is the convoy effect?

A short process can be stuck behind a long process that arrived first, making the short process wait a long time. This increases average waiting time and is a major weakness of FCFS.

### 17. How does SJF work?

Shortest Job First selects, among the processes that have arrived, the one with the smallest burst time and runs it to completion (in this non-preemptive version).

### 18. What are the advantages of SJF?

It usually gives lower average waiting and turnaround times than FCFS because short jobs are completed early. For a batch of processes all available at time 0, non-preemptive SJF minimises average waiting time.

### 19. What are the disadvantages of SJF?

The OS usually does not know the next CPU burst in advance, so it must be estimated. Long jobs can starve if short jobs keep arriving. SJF is not guaranteed to be optimal when arrival times are arbitrary.

### 20. How does Priority Scheduling work in this project?

Among the processes that have arrived, the one with the smallest priority number runs to completion. It is non-preemptive. Ties are broken by arrival time and then Process ID.

### 21. Why does a lower priority number mean higher priority here?

That convention was chosen for the project (and matches the common “nice value” intuition): priority `1` is more important than priority `5`. The code sorts by `priority` ascending.

### 22. What is starvation in priority scheduling?

A low-priority process may wait forever if higher-priority processes keep arriving. Aging is a common solution: increase a waiting process's priority over time. Aging is **not** implemented in this project.

### 23. How does Round Robin work?

The ready queue is FIFO. A process runs for at most one quantum. If it finishes, it leaves; otherwise it is preempted and placed at the back of the queue. Newly arrived processes join the queue according to the arrival/PID rule.

### 24. What happens if the Round Robin quantum is too small?

The CPU switches very often. Response time may improve, but the overhead of context switching increases. Because this project ignores switching cost, very small quanta only change the schedule, not the measured overhead.

### 25. What happens if the quantum is too large?

Round Robin behaves more like FCFS: processes finish before being preempted. If the quantum is at least as large as every burst, the schedule is identical to FCFS.

### 26. Is Round Robin preemptive?

Yes. A timer interrupt at the end of each quantum can preempt the running process. This project models that event in the `round_robin()` loop.

### 27. Is this Round Robin the same as preemptive SJF?

No. Round Robin uses a fixed time quantum and a FIFO ready queue. Preemptive SJF (SRTF) is a different policy that compares remaining burst times at every arrival. Both are implemented here, but their selection rules are independent.

### 28. Why doesn't this project implement multilevel queues or multilevel feedback queues?

The brief asks for five specific single-core algorithms and prioritises simplicity and explainability. Multilevel queues would add complexity without improving the demonstration of the required concepts.

### 29. What is throughput?

Throughput is the number of processes completed per unit time. This project focuses on TAT, WT, RT and CPU utilization as required; it does not report throughput as a separate metric.

### 30. Which algorithm is “best”?

It depends on the metric. On the sample workload, SRTF has the best average TAT and WT, while Round Robin has the best average RT. All five reach 100% CPU utilization because there are no idle gaps. There is no single best algorithm for every workload.

---

## C. Metrics and formulas

### 31. What is completion time (CT)?

Completion time is the time at which a process finishes its last CPU burst. In the code it is `completion_time`.

### 32. What is turnaround time (TAT)?

`TAT = Completion Time − Arrival Time`. It is the total time from arrival to completion, including waiting and running.

### 33. What is waiting time (WT)?

`WT = TAT − Burst Time`. It is the time a process spent waiting in the ready queue, excluding its own execution.

### 34. What is response time (RT)?

`RT = First CPU Start Time − Arrival Time`. It is how long a process waits before receiving the CPU for the first time.

### 35. What is the difference between waiting time and response time?

Waiting time counts all waiting, including waits between time slices. Response time stops at the **first** CPU allocation. In non-preemptive algorithms they are equal; in Round Robin they usually differ.

### 36. How is CPU utilization calculated?

`CPU utilization = (total busy time ÷ total elapsed time) × 100`. Busy time is the sum of non-idle Gantt blocks; elapsed time is measured from time 0 to the last completion.

### 37. Why is initial idle time included in elapsed time?

Because the CPU was available but did nothing while waiting for the first arrival. If elapsed time started at the first arrival, the reported utilization would hide that idle period. The project includes idle blocks from time 0.

### 38. Why is idle time excluded from the numerator?

Idle time is time during which the CPU is not executing a process. Utilization measures useful CPU work, so only non-idle blocks are counted as busy.

### 39. Calculate the FCFS averages for the sample.

FCFS completion times are 4, 7, 8, 10, 15. TAT values are 4, 6, 6, 7, 11, so average TAT = 34/5 = **6.80**. WT values are 0, 3, 5, 5, 6, so average WT = 19/5 = **3.80**. Because FCFS is non-preemptive, average RT is also **3.80**.

### 40. Why is Round Robin's average response time better than SJF's and SRTF's on the sample?

Round Robin interrupts long jobs at a fixed quantum, so P2, P3, P4 and P5 get their first CPU turn earlier. Its average RT is 2.40, versus 2.80 for SRTF and 3.20 for SJF. However, the extra interruptions delay completion, so Round Robin's average TAT (7.60) is worse than SRTF's (6.00) and SJF's (6.20).

### 41. Why do all five algorithms show 100% CPU utilization on the sample?

The sample has no idle gaps: at least one process is ready from time 0 until time 15. Busy time is therefore 15 and elapsed time is 15, giving 100%.

### 42. What is a Gantt chart?

A Gantt chart is a timeline that shows which process used the CPU during each interval. Each block is labelled with a process and bounded by start and end times; an idle block represents no work.

### 43. How is the Gantt chart generated in this project?

Each algorithm produces a list of blocks `{"pid", "start", "end"}`. `merge_timeline()` merges adjacent blocks of the same process. `gantt.js` creates one DOM block per timeline entry, sets `flex-grow` to the duration, and creates a matching axis row.

### 44. Why are Round Robin blocks sometimes merged?

A process can run in consecutive slices when no other process is ready (for example, one process with quantum 2 runs 0–2, 2–4, 4–5). The requirement asks for one merged block `0–5`, which is easier to read and does not change any metric.

### 45. Can turnaround time be less than burst time?

No, for a valid process: it cannot finish before it has executed its full burst, so `TAT = waiting + burst ≥ burst`. The code follows the formulas, so this invariant holds.

---

## D. Data structures and complexity

### 46. Which data structure is used for the Round Robin ready queue?

A `collections.deque`, which supports O(1) append at the right and pop from the left.

### 47. Why use a deque instead of a Python list?

Popping the first element of a list is O(n) because the remaining elements shift. `deque.popleft()` is O(1), which matches the FIFO behaviour of a ready queue.

### 48. What is the `remaining` dictionary used for?

It maps each PID to its remaining burst time in Round Robin. It avoids modifying the original process dictionaries and makes the “run for min(quantum, remaining)” step simple.

### 49. What is the `records` dictionary used for?

It stores each process's start and completion time while the algorithm runs. At the end, `_build_result()` converts it into a list in the original input order.

### 50. What is the time complexity of FCFS?

`O(n log n)` because of the initial sort by arrival and PID, followed by a single `O(n)` pass.

### 51. What is the time complexity of SJF, SRTF and Priority?

SJF and Priority are `O(n²)` in this implementation: each of the `n` rounds scans the pending list to find the available processes and the minimum. SRTF is also `O(n²)`: there are at most `O(n)` arrival/completion events, and each event scans the available list. Heaps could improve these bounds, but the scan is easier to explain.

### 52. What is the time complexity of Round Robin?

`O(n + S)`, where `S` is the number of time slices (at most `sum(burst)/quantum + n`). Queue operations are O(1). The timeline has one block per slice before merging.

### 53. What is the space complexity?

`O(n + B)` where `n` is the number of processes and `B` is the number of timeline blocks. The ready queue, remaining map and records map each hold at most `n` entries.

### 54. Why does `find_best_algorithms` use a tolerance?

Floating-point averages such as `10/3` can differ in the last bits even when mathematically equal. Comparing with `< 1e-9` keeps true ties together.

---

## E. Project implementation

### 55. Which technologies are used?

Python 3 and Flask for the backend, HTML/CSS/vanilla JavaScript for the frontend, a custom Gantt renderer, Chart.js from a CDN for comparison bars, and pytest for tests. There is no frontend framework and no database.

### 56. Why use Flask?

Flask is small and readable. Two JSON endpoints and one HTML route are enough, so a larger framework would add unnecessary complexity for a second-year mini-project.

### 57. Why is the scheduling code in a separate package?

`scheduler/algorithms.py` and `scheduler/metrics.py` contain no Flask imports. They can be tested directly from Python, reused by another interface, and explained without the web layer. `app.py` only validates requests and calls them.

### 58. What are the two API endpoints?

- `POST /api/schedule` runs one chosen algorithm.
- `POST /api/compare` runs all five algorithms on the same list and quantum.
- `GET /` serves the page.

### 59. How does the frontend send data to Flask?

It uses `fetch()` with `Content-Type: application/json` and `JSON.stringify(...)`. The response is parsed with `response.json()` and rendered without reloading the page.

### 60. What does a schedule response contain?

`algorithm_key`, `algorithm`, `quantum`, `timeline`, per-process rows (with start, completion, TAT, WT, RT), and a `metrics` object with averages, utilization, busy time, idle time and total time.

### 61. Where is validation performed?

Both sides. `main.js` checks the form for instant feedback, and `app.py` repeats every check because a client can be bypassed or modified. The server is the authority.

### 62. How are errors displayed without `alert()`?

The page has inline error containers such as `#form-error`, `#run-error` and `#compare-error`. `showError()` sets their `textContent` and makes them visible. They use `role="alert"` for screen readers.

### 63. How is user input kept safe in the page?

Jinja auto-escapes the template, and dynamic table/Gantt labels use `escapeHtml()` or `textContent`. Error messages are inserted with `textContent`, not HTML.

### 64. How does the Gantt chart show proportions?

Each block uses `flex-grow` equal to its duration (`end − start`), and the axis row uses the same values, so block boundaries and time labels align. A minimum block width keeps short slices readable.

### 65. How are tooltips implemented?

A single `.gantt-tooltip` element is created lazily in `gantt.js`. Each block has `mouseenter`, `mousemove`, `mouseleave`, `focus` and `blur` listeners. The tooltip shows the PID, start, end and duration, and flips position near the viewport edge.

### 66. How is the comparison table's best value highlighted?

`/api/compare` returns a `best` object mapping each metric to the winning algorithm names. `renderComparison()` adds the `best` CSS class to those cells and draws the best bars in dark green.

### 67. How are ties handled in the comparison?

`find_best_algorithms()` returns **all** algorithms whose value is equal to the best value within a tiny tolerance. The table highlights every tied cell, and the best-value card shows the names joined with ` / `.

### 68. How does the site handle the Chart.js CDN being unavailable?

`charts.js` checks `typeof Chart === "undefined"` and replaces each chart box with an explanatory fallback. The comparison table and all metrics still work.

### 69. Is any data stored on the server?

No. Each request contains the complete process list, and the server computes a response from scratch. There is no database, session or file storage. Refreshing the page clears the browser state.

### 70. How was the project tested?

`python -m pytest -q` runs 51 automated tests covering algorithms, edge cases, metrics, comparison winners and API validation. The Flask app was also started and tested over real HTTP, and the UI was driven in headless Chrome to verify loading the sample, running FCFS, SRTF and Round Robin, comparison charts, validation errors, and add/edit/delete.

---

## F. Short “explain this code” answers

### 71. Explain the Round Robin “arrival at expiry” rule in one sentence.

When a quantum ends at time `t`, all processes arriving at `t` are added to the ready queue first, and only then is the preempted process appended, so a newly arrived process runs before the process that just used the CPU.

### 72. Why does `round_robin()` use an index into the sorted arrival list?

`next_arrival_index` marks the first process that has not yet entered the ready queue. Because the list is sorted by arrival and PID, a single forward scan enqueues every arrival exactly once in the correct order.

### 73. Why does `_non_preemptive()` sometimes add an Idle block?

When `available` is empty, no process has arrived yet. The algorithm jumps to the minimum arrival time among pending processes and records the gap as `Idle`.

### 74. Why is the process list returned in input order?

`_build_result()` looks up rows by PID in the `records` dictionary and iterates over the original `processes` list. Users see their processes in the order they entered them, even though the algorithm may execute them in a different order.

### 75. What happens if the user edits a process after running a simulation?

`invalidateResults()` hides the old results and clears stored responses. The user must run again, so the page never shows metrics that belong to an older process list.

### 76. Why does the comparison reuse the quantum field even when FCFS is selected?

The comparison always includes Round Robin, so it needs a valid quantum. The UI hides the field for non-RR single runs as required, but the value is still used by **Compare all five**. If it is invalid, the page shows a clear comparison error.

### 77. Why is `Idle` a reserved Process ID?

The Gantt chart and metrics use the string `"Idle"` to identify CPU idle blocks. Allowing a user process with the same ID would make the timeline ambiguous, so both client and server reject it.

### 78. What would you improve next?

Possible extensions: preemptive priority, aging, I/O bursts, multiple cores, CSV import/export, persistence with SQLite, and real measured context-switch overhead. They were deliberately left out to keep the project simple and correct.

---

## G. SRTF extension

### 79. What is SRTF?

Shortest Remaining Time First is the preemptive version of Shortest Job First. At every arrival it compares the remaining CPU time of all ready processes and runs the one with the smallest remaining time.

### 80. What is the difference between SJF and SRTF?

SJF is non-preemptive: once a process starts, it runs to completion. SRTF is preemptive: a newly arrived process with a shorter remaining time can interrupt the running process immediately. SJF is implemented by `sjf()`; SRTF is implemented by `srtf()`.

### 81. When exactly does SRTF preempt a process?

When a new process arrives and its remaining burst is **strictly smaller** than the running process's remaining burst. If the remaining times are equal, the earlier-arrived process keeps the CPU, so no preemption occurs.

### 82. How does SRTF break ties?

It compares `(remaining_time, arrival_time, PID)`. The smallest remaining time wins; if two processes tie, the earlier arrival wins; if they also tie, the smaller Process ID wins.

### 83. How is SRTF implemented in this project?

`srtf()` keeps a `remaining` dictionary (PID → time left), builds an `available` list of arrived unfinished processes at each event, and selects the minimum key. The chosen process runs only until it finishes or the next arrival occurs, then the choice is repeated. First start times and completion times are recorded, and `_build_result()` merges adjacent blocks.

### 84. Why does SRTF beat SJF on the sample workload?

At t=2, P3 arrives with only 1 unit left and preempts P1. P3 completes immediately at t=3, and P1 resumes. This lowers average TAT from 6.20 to 6.00 and average WT from 3.20 to 3.00 compared with non-preemptive SJF. Round Robin still has the best average response time (2.40).

### 85. What is the difference between SRTF and Round Robin?

SRTF chooses dynamically by remaining time, so short jobs always go first. Round Robin uses a fixed quantum and a FIFO queue, so every ready process eventually gets a turn. SRTF can starve a long job if short jobs keep arriving; Round Robin is fairer in that respect.

---

## H. One-line summary for the examiner

> This project is a Flask-served, browser-based simulator that runs FCFS, SJF, SRTF, Round Robin and non-preemptive Priority scheduling in pure Python, returns a merged Gantt timeline and CT/TAT/WT/RT metrics as JSON, and visualises the results with a custom Gantt chart and Chart.js comparison charts. It is a teaching simulation and does not control the real OS scheduler.
