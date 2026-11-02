# Test Cases and Hand-Verified Results

This document records the inputs used to verify the simulator and the numeric results calculated by hand. Every table below was checked with the formulas implemented in `scheduler/metrics.py`:

```text
TAT = Completion Time - Arrival Time
WT  = Turnaround Time - Burst Time
RT  = First CPU Start Time - Arrival Time
CPU Utilisation = Busy Time / Total Elapsed Time × 100
```

Notation used for Gantt charts:

```text
P1 [0–4] → P2 [4–7] → P3 [7–8]
```

Times are whole-number units. `Idle` means no process is ready.

---

## 1. Standard test case (all five algorithms)

### Input

| PID | Arrival | Burst | Priority |
|---|---:|---:|---:|
| P1 | 0 | 4 | 2 |
| P2 | 1 | 3 | 1 |
| P3 | 2 | 1 | 3 |
| P4 | 3 | 2 | 2 |
| P5 | 4 | 5 | 4 |

Round Robin quantum: **2**

This is also the workload loaded by **Load sample** in the website.

### 1.1 FCFS

Order is arrival time, then PID: P1, P2, P3, P4, P5.

**Gantt:**

```text
P1 [0–4] → P2 [4–7] → P3 [7–8] → P4 [8–10] → P5 [10–15]
```

| PID | AT | BT | Start | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 4 | 0 | 4 | 4 | 0 | 0 |
| P2 | 1 | 3 | 4 | 7 | 6 | 3 | 3 |
| P3 | 2 | 1 | 7 | 8 | 6 | 5 | 5 |
| P4 | 3 | 2 | 8 | 10 | 7 | 5 | 5 |
| P5 | 4 | 5 | 10 | 15 | 11 | 6 | 6 |

- Average TAT = (4 + 6 + 6 + 7 + 11) / 5 = 34 / 5 = **6.80**
- Average WT = (0 + 3 + 5 + 5 + 6) / 5 = 19 / 5 = **3.80**
- Average RT = (0 + 3 + 5 + 5 + 6) / 5 = 19 / 5 = **3.80**
- Busy = 15, elapsed = 15, utilization = **100.00%**

### 1.2 SJF (non-preemptive)

At t=0 only P1 is available, so P1 runs to 4. Then the available bursts are P3=1, P4=2, P2=3, P5=5.

**Gantt:**

```text
P1 [0–4] → P3 [4–5] → P4 [5–7] → P2 [7–10] → P5 [10–15]
```

| PID | AT | BT | Start | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 4 | 0 | 4 | 4 | 0 | 0 |
| P2 | 1 | 3 | 7 | 10 | 9 | 6 | 6 |
| P3 | 2 | 1 | 4 | 5 | 3 | 2 | 2 |
| P4 | 3 | 2 | 5 | 7 | 4 | 2 | 2 |
| P5 | 4 | 5 | 10 | 15 | 11 | 6 | 6 |

- Average TAT = (4 + 9 + 3 + 4 + 11) / 5 = 31 / 5 = **6.20**
- Average WT = (0 + 6 + 2 + 2 + 6) / 5 = 16 / 5 = **3.20**
- Average RT = same as WT because the algorithm is non-preemptive = **3.20**
- Utilization = **100.00%**

### 1.3 SRTF (preemptive SJF)

P1 starts alone at t=0. P3 arrives at t=2 with only 1 unit left, which is shorter than P1's 2, so P3 preempts P1. At t=3, P1 and the newly arrived P4 both have 2 units remaining; P1 continues because it arrived earlier.

**Gantt:**

```text
P1 [0–2] → P3 [2–3] → P1 [3–5] → P4 [5–7] → P2 [7–10] → P5 [10–15]
```

| PID | AT | BT | Start | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 4 | 0 | 5 | 5 | 1 | 0 |
| P2 | 1 | 3 | 7 | 10 | 9 | 6 | 6 |
| P3 | 2 | 1 | 2 | 3 | 1 | 0 | 0 |
| P4 | 3 | 2 | 5 | 7 | 4 | 2 | 2 |
| P5 | 4 | 5 | 10 | 15 | 11 | 6 | 6 |

- Average TAT = (5 + 9 + 1 + 4 + 11) / 5 = 30 / 5 = **6.00**
- Average WT = (1 + 6 + 0 + 2 + 6) / 5 = 15 / 5 = **3.00**
- Average RT = (0 + 6 + 0 + 2 + 6) / 5 = 14 / 5 = **2.80**
- Utilization = **100.00%**

### 1.4 Priority (non-preemptive, lower number = higher priority)

P1 (priority 2) is the only arrival at t=0. At t=4 the available priorities are P2=1, P4=2, P3=3, P5=4.

**Gantt:**

```text
P1 [0–4] → P2 [4–7] → P4 [7–9] → P3 [9–10] → P5 [10–15]
```

| PID | AT | BT | Priority | Start | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 4 | 2 | 0 | 4 | 4 | 0 | 0 |
| P2 | 1 | 3 | 1 | 4 | 7 | 6 | 3 | 3 |
| P3 | 2 | 1 | 3 | 9 | 10 | 8 | 7 | 7 |
| P4 | 3 | 2 | 2 | 7 | 9 | 6 | 4 | 4 |
| P5 | 4 | 5 | 4 | 10 | 15 | 11 | 6 | 6 |

- Average TAT = (4 + 6 + 8 + 6 + 11) / 5 = 35 / 5 = **7.00**
- Average WT = (0 + 3 + 7 + 4 + 6) / 5 = 20 / 5 = **4.00**
- Average RT = **4.00**
- Utilization = **100.00%**

### 1.5 Round Robin, quantum 2

Queue trace:

| Time | Action | Ready queue after action |
|---:|---|---|
| 0 | P1 runs 0–2; P2 and P3 arrive during the slice | `[P2, P3, P1]` |
| 2 | P2 runs 2–4; P4 and P5 arrive during the slice | `[P3, P1, P4, P5, P2]` |
| 4 | P3 runs 4–5 and finishes | `[P1, P4, P5, P2]` |
| 5 | P1 runs 5–7 and finishes | `[P4, P5, P2]` |
| 7 | P4 runs 7–9 and finishes | `[P5, P2]` |
| 9 | P5 runs 9–11 | `[P2, P5]` |
| 11 | P2 runs 11–12 and finishes | `[P5]` |
| 12 | P5 runs 12–14 | `[P5]` |
| 14 | P5 runs 14–15 and finishes | `[]` |

The last two P5 blocks (12–14 and 14–15) are merged in the Gantt output.

**Gantt (merged):**

```text
P1 [0–2] → P2 [2–4] → P3 [4–5] → P1 [5–7] → P4 [7–9] → P5 [9–11] → P2 [11–12] → P5 [12–15]
```

| PID | AT | BT | Start | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 4 | 0 | 7 | 7 | 3 | 0 |
| P2 | 1 | 3 | 2 | 12 | 11 | 8 | 1 |
| P3 | 2 | 1 | 4 | 5 | 3 | 2 | 2 |
| P4 | 3 | 2 | 7 | 9 | 6 | 4 | 4 |
| P5 | 4 | 5 | 9 | 15 | 11 | 6 | 5 |

- Average TAT = (7 + 11 + 3 + 6 + 11) / 5 = 38 / 5 = **7.60**
- Average WT = (3 + 8 + 2 + 4 + 6) / 5 = 23 / 5 = **4.60**
- Average RT = (0 + 1 + 2 + 4 + 5) / 5 = 12 / 5 = **2.40**
- Utilization = **100.00%**

### 1.6 Comparison summary

| Algorithm | Avg TAT | Avg WT | Avg RT | CPU util |
|---|---:|---:|---:|---:|
| FCFS | 6.80 | 3.80 | 3.80 | 100.00% |
| SJF | 6.20 | 3.20 | 3.20 | 100.00% |
| SRTF | 6.00 | 3.00 | 2.80 | 100.00% |
| Round Robin (q=2) | 7.60 | 4.60 | 2.40 | 100.00% |
| Priority | 7.00 | 4.00 | 4.00 | 100.00% |

Winners: **SRTF** for TAT and WT, **Round Robin** for RT, and **all five** for CPU utilization.

---

## 2. Single process with initial idle

### Input

| PID | Arrival | Burst | Priority |
|---|---:|---:|---:|
| P1 | 3 | 4 | 1 |

Quantum: 2

### Expected for FCFS, SJF, SRTF and Priority

```text
Idle [0–3] → P1 [3–7]
```

### Expected for Round Robin

Internally P1 runs 3–5 and 5–7. The adjacent blocks are merged:

```text
Idle [0–3] → P1 [3–7]
```

| Metric | Value |
|---|---:|
| CT | 7 |
| TAT | 7 − 3 = 4 |
| WT | 4 − 4 = 0 |
| RT | 3 − 3 = 0 |
| Average TAT | 4.00 |
| Average WT | 0.00 |
| Average RT | 0.00 |
| Busy time | 4 |
| Idle time | 3 |
| Total elapsed | 7 |
| CPU utilization | 4 / 7 × 100 = **57.14%** |

This case verifies that initial idle time is included in elapsed time but excluded from the numerator.

---

## 3. Simultaneous arrivals

### Input

| PID | Arrival | Burst | Priority |
|---|---:|---:|---:|
| P1 | 0 | 2 | 3 |
| P2 | 0 | 1 | 1 |
| P3 | 0 | 1 | 2 |

All three arrive together, so the tie-break rule decides the order.

### 3.1 FCFS

Equal arrival times → smaller PID first: P1, P2, P3.

```text
P1 [0–2] → P2 [2–3] → P3 [3–4]
```

| PID | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|
| P1 | 2 | 2 | 0 | 0 |
| P2 | 3 | 3 | 2 | 2 |
| P3 | 4 | 4 | 3 | 3 |

Averages: TAT **3.00**, WT **1.67**, RT **1.67**. Utilization **100%**.

### 3.2 SJF

Equal bursts for P2 and P3 → smaller PID P2 first; then P3; then P1.

```text
P2 [0–1] → P3 [1–2] → P1 [2–4]
```

| PID | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|
| P1 | 4 | 4 | 2 | 2 |
| P2 | 1 | 1 | 0 | 0 |
| P3 | 2 | 2 | 1 | 1 |

Averages: TAT = 7/3 = **2.33**, WT = 3/3 = **1.00**, RT = **1.00**. Utilization **100%**.

### 3.3 Priority

Priorities are P2=1, P3=2, P1=3.

```text
P2 [0–1] → P3 [1–2] → P1 [2–4]
```

Same metrics as SJF for this input: TAT **2.33**, WT **1.00**, RT **1.00**.

### 3.4 SRTF

All three are available at t=0. P2 and P3 have the smallest remaining time (1); P2 has the smaller PID, so P2 runs, then P3, then P1.

```text
P2 [0–1] → P3 [1–2] → P1 [2–4]
```

Same metrics as SJF/Priority for this input: TAT **2.33**, WT **1.00**, RT **1.00**, utilization **100%**.

### 3.5 Round Robin, quantum 2

All arrive at 0, ordered P1, P2, P3. P1's burst equals the quantum, so it finishes without preemption; P2 and P3 then run.

```text
P1 [0–2] → P2 [2–3] → P3 [3–4]
```

Same as FCFS: TAT **3.00**, WT **1.67**, RT **1.67**, utilization **100%**.

---

## 4. Idle gap between processes

### Input

| PID | Arrival | Burst | Priority |
|---|---:|---:|---:|
| P1 | 0 | 2 | 1 |
| P2 | 5 | 3 | 2 |
| P3 | 6 | 1 | 3 |

Quantum: 2

### 4.1 FCFS, SJF and Priority

At t=2 the CPU is idle until P2 arrives at 5. P3 arrives at 6 but is non-preemptive, so it waits for P2.

```text
P1 [0–2] → Idle [2–5] → P2 [5–8] → P3 [8–9]
```

| PID | AT | BT | Start | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 2 | 0 | 2 | 2 | 0 | 0 |
| P2 | 5 | 3 | 5 | 8 | 3 | 0 | 0 |
| P3 | 6 | 1 | 8 | 9 | 3 | 2 | 2 |

- Average TAT = 8/3 = **2.67**
- Average WT = 2/3 = **0.67**
- Average RT = 2/3 = **0.67**
- Busy = 6, idle = 3, elapsed = 9 → utilization = **66.67%**

### 4.2 Round Robin, quantum 2

P2 runs 5–7. At t=7, P3 (arrived at 6) is enqueued before the preempted P2.

```text
P1 [0–2] → Idle [2–5] → P2 [5–7] → P3 [7–8] → P2 [8–9]
```

| PID | AT | BT | Start | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 2 | 0 | 2 | 2 | 0 | 0 |
| P2 | 5 | 3 | 5 | 9 | 4 | 1 | 0 |
| P3 | 6 | 1 | 7 | 8 | 2 | 1 | 1 |

- Average TAT = 8/3 = **2.67**
- Average WT = 2/3 = **0.67**
- Average RT = 1/3 = **0.33**
- Utilization = **66.67%**

### 4.3 SRTF

P2 starts at t=5. At t=6, P3 arrives with only 1 unit remaining, while P2 has 2 left, so P3 preempts P2. P2 then resumes at t=7.

```text
P1 [0–2] → Idle [2–5] → P2 [5–6] → P3 [6–7] → P2 [7–9]
```

| PID | AT | BT | Start | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 2 | 0 | 2 | 2 | 0 | 0 |
| P2 | 5 | 3 | 5 | 9 | 4 | 1 | 0 |
| P3 | 6 | 1 | 6 | 7 | 1 | 0 | 0 |

- Average TAT = 7/3 = **2.33**
- Average WT = 1/3 = **0.33**
- Average RT = 0/3 = **0.00**
- Busy = 6, idle = 3, elapsed = 9 → utilization = **66.67%**

---

## 5. SRTF preemption and equal-remaining tie

### 5.1 Shorter arrival preempts the running process

**Input**

| PID | Arrival | Burst | Priority |
|---|---:|---:|---:|
| P1 | 0 | 7 | 1 |
| P2 | 2 | 2 | 2 |

At t=2, P1 has 5 units left while P2 needs only 2, so P2 preempts P1. P1 resumes at t=4.

```text
P1 [0–2] → P2 [2–4] → P1 [4–9]
```

| PID | AT | BT | Start | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 7 | 0 | 9 | 9 | 2 | 0 |
| P2 | 2 | 2 | 2 | 4 | 2 | 0 | 0 |

- Average TAT = 11/2 = **5.50**
- Average WT = 2/2 = **1.00**
- Average RT = 0/2 = **0.00**
- Utilization = **100%**

### 5.2 Equal remaining time does not preempt

**Input**

| PID | Arrival | Burst | Priority |
|---|---:|---:|---:|
| P1 | 0 | 4 | 1 |
| P2 | 2 | 2 | 2 |

At t=2 both processes have 2 units remaining. The tie-break rule prefers the earlier arrival, so P1 keeps the CPU.

```text
P1 [0–4] → P2 [4–6]
```

| PID | AT | BT | Start | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 4 | 0 | 4 | 4 | 0 | 0 |
| P2 | 2 | 2 | 4 | 6 | 4 | 2 | 2 |

- Average TAT = 8/2 = **4.00**
- Average WT = 2/2 = **1.00**
- Average RT = 2/2 = **1.00**
- Utilization = **100%**

If the implementation incorrectly preempted on equal remaining time, P2 would run 2–4 and P1 4–6, giving P2 a response time of 0. The automated test checks the exact timeline.

---

## 6. Equal burst tie (SJF)

### Input

| PID | Arrival | Burst | Priority |
|---|---:|---:|---:|
| P1 | 0 | 5 | 2 |
| P2 | 1 | 2 | 3 |
| P3 | 1 | 2 | 1 |

P2 and P3 have the same burst and arrival. The smaller PID is P2, so SJF chooses P2 first even though P3 has the better priority (priority is irrelevant to SJF).

```text
P1 [0–5] → P2 [5–7] → P3 [7–9]
```

| PID | AT | BT | Start | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 5 | 0 | 5 | 5 | 0 | 0 |
| P2 | 1 | 2 | 5 | 7 | 6 | 4 | 4 |
| P3 | 1 | 2 | 7 | 9 | 8 | 6 | 6 |

Average TAT = 19/3 = **6.33**, average WT = 10/3 = **3.33**, average RT = **3.33**, utilization **100%**.

---

## 7. Equal priority tie (Priority Scheduling)

### Input

| PID | Arrival | Burst | Priority |
|---|---:|---:|---:|
| P1 | 0 | 3 | 2 |
| P2 | 1 | 2 | 1 |
| P3 | 1 | 1 | 1 |

P2 and P3 have the same priority and arrival. The smaller PID P2 wins, even though P3 has the shorter burst.

```text
P1 [0–3] → P2 [3–5] → P3 [5–6]
```

| PID | AT | BT | Priority | Start | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 3 | 2 | 0 | 3 | 3 | 0 | 0 |
| P2 | 1 | 2 | 1 | 3 | 5 | 4 | 2 | 2 |
| P3 | 1 | 1 | 1 | 5 | 6 | 5 | 4 | 4 |

Average TAT = 12/3 = **4.00**, average WT = 6/3 = **2.00**, average RT = **2.00**, utilization **100%**.

If this were SJF, P3 (burst 1) would run before P2 (burst 2), producing a different Gantt chart. This is why the test asserts P2 first.

---

## 8. Quantum larger than every burst

Input: the standard sample from section 1, quantum **100**.

Because every burst is smaller than 100, no process is ever preempted. Round Robin therefore behaves like FCFS:

```text
P1 [0–4] → P2 [4–7] → P3 [7–8] → P4 [8–10] → P5 [10–15]
```

All metrics are identical to FCFS:

| Metric | Value |
|---|---:|
| Average TAT | 6.80 |
| Average WT | 3.80 |
| Average RT | 3.80 |
| CPU utilization | 100.00% |

The automated test compares both the entire timeline and the entire metrics dictionary for equality.

---

## 9. Quantum of 1

### Input

| PID | Arrival | Burst | Priority |
|---|---:|---:|---:|
| P1 | 0 | 2 | 1 |
| P2 | 1 | 2 | 2 |

### Trace

| Time | Action | Queue after action |
|---:|---|---|
| 0 | P1 runs 0–1 | `[P2, P1]` |
| 1 | P2 runs 1–2 | `[P1, P2]` |
| 2 | P1 runs 2–3 and finishes | `[P2]` |
| 3 | P2 runs 3–4 and finishes | `[]` |

```text
P1 [0–1] → P2 [1–2] → P1 [2–3] → P2 [3–4]
```

| PID | AT | BT | Start | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 2 | 0 | 3 | 3 | 1 | 0 |
| P2 | 1 | 2 | 1 | 4 | 3 | 1 | 0 |

- Average TAT = 6/2 = **3.00**
- Average WT = 2/2 = **1.00**
- Average RT = 0/2 = **0.00**
- Utilization = **100%**

The key observation is that P2's response time is 0, not 1, because it starts at time 1 and also arrived at time 1.

---

## 10. Arrival exactly at quantum expiry (Round Robin ordering rule)

### Input

| PID | Arrival | Burst | Priority |
|---|---:|---:|---:|
| P1 | 0 | 3 | 1 |
| P2 | 2 | 1 | 2 |

Quantum: 2

P1's first quantum expires at t=2, which is exactly P2's arrival time. The rule says P2 enters the ready queue **before** P1 is re-added.

### Expected

```text
P1 [0–2] → P2 [2–3] → P1 [3–4]
```

| PID | AT | BT | Start | CT | TAT | WT | RT |
|---|---:|---:|---:|---:|---:|---:|---:|
| P1 | 0 | 3 | 0 | 4 | 4 | 1 | 0 |
| P2 | 2 | 1 | 2 | 3 | 1 | 0 | 0 |

- Average TAT = 5/2 = **2.50**
- Average WT = 1/2 = **0.50**
- Average RT = 0/2 = **0.00**
- Utilization = **100%**

Incorrect ordering would produce `P1 [0–3] → P2 [3–4]`, giving P2 a response time of 1 and changing completion times. The automated test asserts the exact timeline, so this rule cannot silently regress.

---

## 11. Validation cases

All messages below come from `app.py` and are shown inline in the browser. No browser `alert()` is used.

| Submitted input | Expected HTTP status | Expected error message |
|---|---:|---|
| `{"processes": [], "algorithm": "fcfs"}` | 400 | `Add at least one process before running the simulation.` |
| `{"algorithm": "fcfs"}` (no list) | 400 | `No process list was received. Add at least one process.` |
| `processes` is a string | 400 | `The process list must be an array of processes.` |
| `algorithm` missing/invalid | 400 | `Choose a valid algorithm: fcfs, sjf, srtf, rr or priority.` |
| `algorithm: "rr"` without quantum | 400 | `Time quantum is required.` |
| `algorithm: "rr", quantum: 0` | 400 | `Time quantum must be greater than 0.` |
| Arrival `-1` | 400 | `Process 'P1': Arrival time cannot be negative.` |
| Burst `0` | 400 | `Process 'P1': Burst time must be greater than 0.` |
| Priority `-1` | 400 | `Process 'P1': Priority cannot be negative.` |
| Arrival `"abc"` | 400 | `Process 'P1': Arrival time must be a whole number.` |
| Burst `2.5` | 400 | `Process 'P1': Burst time must be a whole number.` |
| Missing priority | 400 | `Process 'P1': Priority is required.` |
| Empty PID `""` | 400 | `Process #1: Process ID is required.` |
| PID `"Idle"` | 400 | `The Process ID 'Idle' is reserved for idle CPU time. Choose another ID.` |
| PID `"P 1"` (space) | 400 | `Process ID 'P 1' is invalid. Use 1-16 letters, numbers, hyphens or underscores.` |
| PIDs `"P1"` and `"p1"` | 400 | `Duplicate Process ID 'p1'. Every process needs a unique ID.` |
| More than 100 processes | 400 | `A maximum of 100 processes is supported.` |
| Non-JSON body | 400 | `Send a JSON object with a 'processes' array.` |

Client-side checks mirror these rules, so the user usually sees the message before a request is sent. The server remains the authority.

---

## 12. Automated test coverage

Run:

```powershell
python -m pytest -q
```

Actual final output:

```text
51 passed in 1.74s
```

Timing varies slightly by machine; the test count and results do not.

| Area | Tests |
|---|---|
| PID natural ordering | `test_pid_sort_key_orders_numbers_naturally` |
| Gantt merging | `test_merge_timeline_joins_only_touching_blocks_of_same_process`, `test_round_robin_merges_consecutive_blocks` |
| Standard sample | `test_fcfs_sample`, `test_sjf_sample`, `test_srtf_sample`, `test_priority_sample`, `test_round_robin_sample` |
| SRTF behaviour | `test_srtf_preempts_when_shorter_process_arrives`, `test_srtf_equal_remaining_time_does_not_preempt_earlier_process`, `test_srtf_simultaneous_arrivals_use_remaining_then_pid`, `test_srtf_idle_gap_and_resumption` |
| RR expiry ordering | `test_round_robin_arrival_at_expiry_enters_before_preempted_process` |
| Quantum edges | `test_round_robin_quantum_larger_than_every_burst_matches_fcfs`, `test_round_robin_quantum_one`, `test_round_robin_rejects_invalid_quantum` |
| Idle gaps | `test_idle_gap_non_preemptive[fcfs/sjf/priority_scheduling]`, `test_idle_gap_round_robin`, `test_srtf_idle_gap_and_resumption`, `test_single_process_with_initial_idle` |
| Ties and simultaneous arrivals | `test_sjf_equal_burst_tie_uses_arrival_then_pid`, `test_priority_tie_ignores_burst_and_uses_pid`, `test_fcfs_simultaneous_arrivals_are_sorted_by_pid`, `test_sjf_and_priority_simultaneous_arrivals`, `test_srtf_simultaneous_arrivals_use_remaining_then_pid` |
| Best algorithm / ties | `test_find_best_algorithms_on_sample`, `test_find_best_algorithms_keeps_ties` |
| Web page and assets | `test_index_page_loads`, `test_static_assets_load` |
| API success | `test_api_schedule_fcfs`, `test_api_schedule_round_robin`, `test_api_schedule_srtf`, `test_api_compare` |
| API validation | `test_api_schedule_rejects_bad_settings` (6 parameter cases), `test_api_rejects_invalid_process_fields` (9 cases), `test_api_rejects_duplicate_pids_case_insensitively`, `test_api_compare_requires_quantum`, `test_api_rejects_non_json_body` |

The test file is `tests/test_algorithms.py`.

---

## 13. Live server and browser verification

The Flask app was actually started during development (not only exercised through the pytest client), and the endpoints were called over HTTP:

```text
GET  /                            -> 200
GET  /static/css/style.css        -> 200
GET  /static/js/main.js           -> 200
POST /api/schedule (FCFS)         -> 200 | avg TAT: 6.8 | blocks: 5
POST /api/schedule (SRTF)         -> 200 | avg TAT: 6.0 | avg WT: 3.0 | avg RT: 2.8 | blocks: 6
POST /api/schedule (RR q=2)       -> 200 | avg RT: 2.4  | blocks: 8
POST /api/compare                 -> 200 | algorithms: FCFS, SJF, SRTF, Round Robin, Priority
POST /api/schedule (empty list)   -> 400 | Add at least one process before running the simulation.
POST /api/compare (no quantum)    -> 400 | Time quantum is required.
```

The page was then driven in headless Chrome:

- sample workload loaded → 5 table rows
- FCFS → average TAT 6.80, WT 3.80, RT 3.80, utilization 100.00%, 5 Gantt blocks
- SRTF → average TAT 6.00, WT 3.00, RT 2.80, utilization 100.00%, 6 Gantt blocks
- Round Robin q=2 → average TAT 7.60, WT 4.60, RT 2.40, 8 Gantt blocks
- comparison → 5 table rows, 4 best-value cards, 3 Chart.js charts with labels `FCFS / SJF / SRTF / RR (q=2) / Priority` and values `[3.8, 3.2, 3.0, 4.6, 4]`, `[6.8, 6.2, 6.0, 7.6, 7]`, `[3.8, 3.2, 2.8, 2.4, 4]`
- empty-list run → inline error, results hidden
- add / duplicate error / edit / delete all behaved correctly
- mobile width 390 px → no page-level horizontal overflow
- browser console → 0 severe messages

These checks confirm that the frontend and backend work together, not just individually.
