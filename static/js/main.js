/*
 * static/js/main.js
 * -----------------
 * Browser-side controller for the CPU Scheduler Simulator.
 *
 * Responsibilities:
 *   1. Keep the process list in memory and render the editable table.
 *   2. Validate the process form and show inline messages (no alert()).
 *   3. Send the list to /api/schedule or /api/compare with fetch().
 *   4. Render the result metrics, Gantt chart, comparison table and charts.
 */
(function () {
    "use strict";

    var SAMPLE_PROCESSES = [
        { pid: "P1", arrival: 0, burst: 4, priority: 2 },
        { pid: "P2", arrival: 1, burst: 3, priority: 1 },
        { pid: "P3", arrival: 2, burst: 1, priority: 3 },
        { pid: "P4", arrival: 3, burst: 2, priority: 2 },
        { pid: "P5", arrival: 4, burst: 5, priority: 4 }
    ];

    var state = {
        processes: [],
        editIndex: null,
        selectedAlgorithm: "fcfs",
        lastResult: null,
        lastComparison: null
    };

    var elements = {
        form: document.getElementById("process-form"),
        pid: document.getElementById("pid"),
        arrival: document.getElementById("arrival"),
        burst: document.getElementById("burst"),
        priority: document.getElementById("priority"),
        submit: document.getElementById("process-submit"),
        cancel: document.getElementById("cancel-edit"),
        modeHint: document.getElementById("form-mode-hint"),
        formError: document.getElementById("form-error"),
        notice: document.getElementById("process-notice"),
        processCount: document.getElementById("process-count"),
        processTbody: document.getElementById("process-tbody"),
        loadSample: document.getElementById("load-sample"),
        heroSample: document.getElementById("hero-sample"),
        clear: document.getElementById("clear-processes"),
        algoCards: Array.prototype.slice.call(document.querySelectorAll(".algo-card")),
        quantumField: document.getElementById("quantum-field"),
        quantum: document.getElementById("quantum"),
        runButton: document.getElementById("run-button"),
        runError: document.getElementById("run-error"),
        resultsEmpty: document.getElementById("results-empty"),
        resultsContent: document.getElementById("results-content"),
        resultBadge: document.getElementById("result-badge"),
        metricTat: document.getElementById("metric-tat"),
        metricWt: document.getElementById("metric-wt"),
        metricRt: document.getElementById("metric-rt"),
        metricUtil: document.getElementById("metric-util"),
        metricTimeNote: document.getElementById("metric-time-note"),
        ganttSubtitle: document.getElementById("gantt-subtitle"),
        ganttTotal: document.getElementById("gantt-total"),
        ganttContainer: document.getElementById("gantt-container"),
        ganttLegend: document.getElementById("gantt-legend"),
        resultTbody: document.getElementById("result-tbody"),
        compareButton: document.getElementById("compare-button"),
        compareError: document.getElementById("compare-error"),
        compareEmpty: document.getElementById("compare-empty"),
        compareContent: document.getElementById("compare-content"),
        compareBadge: document.getElementById("compare-badge"),
        bestCallouts: document.getElementById("best-callouts"),
        compareTbody: document.getElementById("compare-tbody")
    };

    var reducedMotion = window.matchMedia
        ? window.matchMedia("(prefers-reduced-motion: reduce)").matches
        : false;

    /* ----------------------------- Helpers ----------------------------- */

    function escapeHtml(value) {
        return String(value).replace(/[&<>"']/g, function (character) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#039;"
            }[character];
        });
    }

    function formatNumber(value, digits) {
        var places = digits === undefined ? 2 : digits;
        if (typeof value !== "number" || !isFinite(value)) {
            return "\u2014";
        }
        return value.toFixed(places);
    }

    function formatCell(value) {
        return Number.isInteger(value) ? String(value) : formatNumber(value, 2);
    }

    function showError(element, message) {
        element.textContent = message;
        element.hidden = false;
    }

    function hideError(element) {
        element.textContent = "";
        element.hidden = true;
    }

    function showNotice(message) {
        elements.notice.textContent = message;
        elements.notice.hidden = false;
    }

    function hideNotice() {
        elements.notice.textContent = "";
        elements.notice.hidden = true;
    }

    function setButtonBusy(button, isBusy, idleText, busyText) {
        button.disabled = isBusy;
        button.textContent = isBusy ? busyText : idleText;
        button.setAttribute("aria-busy", isBusy ? "true" : "false");
    }

    function scrollToElement(element) {
        element.scrollIntoView({
            behavior: reducedMotion ? "auto" : "smooth",
            block: "start"
        });
    }

    function readIntegerField(input, label, minimum, rangeMessage) {
        var text = input.value.trim();
        if (text === "") {
            throw new Error(label + " is required.");
        }
        if (!/^[+-]?\d+$/.test(text)) {
            throw new Error(label + " must be a whole number.");
        }

        var value = Number(text);
        if (!Number.isSafeInteger(value)) {
            throw new Error(label + " is too large.");
        }
        if (value < minimum) {
            throw new Error(rangeMessage);
        }
        return value;
    }

    /* --------------------------- Process table -------------------------- */

    function renderProcessTable() {
        var count = state.processes.length;
        elements.processCount.textContent = count + (count === 1 ? " process" : " processes");

        if (count === 0) {
            elements.processTbody.innerHTML =
                '<tr><td colspan="5" class="empty-cell">No processes yet. Add one above or load the sample workload.</td></tr>';
            return;
        }

        elements.processTbody.innerHTML = state.processes.map(function (process, index) {
            return (
                "<tr>" +
                '<td><span class="pid-chip">' + escapeHtml(process.pid) + "</span></td>" +
                '<td class="num">' + process.arrival + "</td>" +
                '<td class="num">' + process.burst + "</td>" +
                '<td class="num">' + process.priority + "</td>" +
                '<td><div class="row-actions">' +
                '<button type="button" class="icon-btn" data-action="edit" data-index="' + index +
                '" aria-label="Edit ' + escapeHtml(process.pid) + '">Edit</button>' +
                '<button type="button" class="icon-btn danger" data-action="delete" data-index="' + index +
                '" aria-label="Delete ' + escapeHtml(process.pid) + '">Delete</button>' +
                "</div></td>" +
                "</tr>"
            );
        }).join("");
    }

    function readProcessForm() {
        var pid = elements.pid.value.trim();

        if (pid === "") {
            throw new Error("Process ID is required.");
        }
        if (!/^[A-Za-z0-9_-]{1,16}$/.test(pid)) {
            throw new Error("Process ID must be 1-16 letters, numbers, hyphens or underscores.");
        }
        if (pid.toLowerCase() === "idle") {
            throw new Error("The ID 'Idle' is reserved for idle CPU time. Choose another ID.");
        }

        var arrival = readIntegerField(
            elements.arrival,
            "Arrival time",
            0,
            "Arrival time cannot be negative."
        );
        var burst = readIntegerField(
            elements.burst,
            "Burst time",
            1,
            "Burst time must be greater than 0."
        );
        var priority = readIntegerField(
            elements.priority,
            "Priority",
            0,
            "Priority cannot be negative."
        );

        return { pid: pid, arrival: arrival, burst: burst, priority: priority };
    }

    function resetForm() {
        state.editIndex = null;
        elements.form.reset();
        elements.submit.textContent = "Add process";
        elements.cancel.hidden = true;
        elements.modeHint.textContent = "The new process is appended to the list.";
        hideError(elements.formError);
    }

    function handleFormSubmit(event) {
        event.preventDefault();
        hideError(elements.formError);
        hideNotice();

        try {
            var values = readProcessForm();
            var duplicate = state.processes.some(function (process, index) {
                return index !== state.editIndex &&
                    process.pid.toLowerCase() === values.pid.toLowerCase();
            });

            if (duplicate) {
                throw new Error('Process ID "' + values.pid + '" already exists. Choose a unique ID.');
            }

            if (state.editIndex === null) {
                state.processes.push(values);
                showNotice(values.pid + " added to the process list.");
            } else {
                var previousPid = state.processes[state.editIndex].pid;
                state.processes[state.editIndex] = values;
                showNotice(previousPid + " updated. Run the simulation again to see the new result.");
            }

            resetForm();
            renderProcessTable();
            invalidateResults();
            elements.pid.focus();
        } catch (error) {
            showError(elements.formError, error.message);
        }
    }

    function startEdit(index) {
        var process = state.processes[index];
        if (!process) {
            return;
        }

        state.editIndex = index;
        elements.pid.value = process.pid;
        elements.arrival.value = String(process.arrival);
        elements.burst.value = String(process.burst);
        elements.priority.value = String(process.priority);

        elements.submit.textContent = "Update process";
        elements.cancel.hidden = false;
        elements.modeHint.textContent =
            "Editing " + process.pid + ". Its position in the list stays the same.";
        hideError(elements.formError);
        hideNotice();

        elements.pid.focus();
        elements.pid.select();
    }

    function handleTableClick(event) {
        var button = event.target.closest("button[data-action]");
        if (!button) {
            return;
        }

        var index = Number(button.getAttribute("data-index"));
        if (!Number.isInteger(index) || index < 0 || index >= state.processes.length) {
            return;
        }

        if (button.getAttribute("data-action") === "edit") {
            startEdit(index);
            return;
        }

        var removedPid = state.processes[index].pid;
        state.processes.splice(index, 1);

        if (state.editIndex !== null) {
            if (state.editIndex === index) {
                resetForm();
            } else if (state.editIndex > index) {
                state.editIndex -= 1;
            }
        }

        renderProcessTable();
        invalidateResults();
        showNotice(removedPid + " removed from the process list.");
    }

    function loadSample() {
        state.processes = SAMPLE_PROCESSES.map(function (process) {
            return {
                pid: process.pid,
                arrival: process.arrival,
                burst: process.burst,
                priority: process.priority
            };
        });

        resetForm();
        renderProcessTable();
        invalidateResults();
        showNotice("Sample workload loaded: 5 processes. Choose an algorithm and run the simulation.");
        scrollToElement(document.getElementById("processes"));
    }

    function clearAllProcesses() {
        if (state.processes.length === 0) {
            showNotice("The process list is already empty.");
            return;
        }

        state.processes = [];
        resetForm();
        renderProcessTable();
        invalidateResults();
        showNotice("All processes cleared.");
    }

    /* ------------------------ Algorithm selection ---------------------- */

    function selectAlgorithm(algorithmKey) {
        state.selectedAlgorithm = algorithmKey;

        elements.algoCards.forEach(function (card) {
            card.classList.toggle("selected", card.getAttribute("data-algo") === algorithmKey);
        });

        elements.quantumField.hidden = algorithmKey !== "rr";
        invalidateResults();
    }

    function readQuantum() {
        return readIntegerField(
            elements.quantum,
            "Time quantum",
            1,
            "Time quantum must be greater than 0."
        );
    }

    /* ------------------------- Result rendering ------------------------ */

    function invalidateResults() {
        state.lastResult = null;
        state.lastComparison = null;

        elements.resultsEmpty.hidden = false;
        elements.resultsContent.hidden = true;
        elements.resultBadge.hidden = true;

        elements.compareEmpty.hidden = false;
        elements.compareContent.hidden = true;

        hideError(elements.runError);
        hideError(elements.compareError);
    }

    function renderResults(data) {
        var metrics = data.metrics;

        elements.resultBadge.textContent =
            data.algorithm + (data.algorithm_key === "rr" ? " \u00b7 quantum " + data.quantum : "");
        elements.resultBadge.hidden = false;

        elements.metricTat.textContent = formatNumber(metrics.avg_turnaround_time);
        elements.metricWt.textContent = formatNumber(metrics.avg_waiting_time);
        elements.metricRt.textContent = formatNumber(metrics.avg_response_time);
        elements.metricUtil.textContent = formatNumber(metrics.cpu_utilization) + "%";
        elements.metricTimeNote.textContent =
            "Busy " + formatCell(metrics.busy_time) +
            " \u00b7 idle " + formatCell(metrics.idle_time) +
            " \u00b7 total " + formatCell(metrics.total_time);

        elements.ganttTotal.textContent = formatCell(metrics.total_time) + " time units";
        elements.ganttSubtitle.textContent = data.algorithm_key === "rr"
            ? "Adjacent blocks of the same process are merged. Quantum = " + data.quantum + "."
            : "Hover or focus a block to see its timing.";

        window.GanttChart.render(data.timeline, elements.ganttContainer, elements.ganttLegend);

        elements.resultTbody.innerHTML = data.processes.map(function (process) {
            return (
                "<tr>" +
                '<td><span class="pid-chip">' + escapeHtml(process.pid) + "</span></td>" +
                '<td class="num">' + formatCell(process.arrival) + "</td>" +
                '<td class="num">' + formatCell(process.burst) + "</td>" +
                '<td class="num">' + formatCell(process.priority) + "</td>" +
                '<td class="num">' + formatCell(process.start_time) + "</td>" +
                '<td class="num">' + formatCell(process.completion_time) + "</td>" +
                '<td class="num">' + formatCell(process.turnaround_time) + "</td>" +
                '<td class="num">' + formatCell(process.waiting_time) + "</td>" +
                '<td class="num">' + formatCell(process.response_time) + "</td>" +
                "</tr>"
            );
        }).join("");

        elements.resultsEmpty.hidden = true;
        elements.resultsContent.hidden = false;
    }

    /* -------------------------- API requests --------------------------- */

    async function postJSON(url, payload) {
        var response;

        try {
            response = await fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        } catch (networkError) {
            throw new Error(
                "Cannot reach the Flask server. Make sure python app.py is running, then try again."
            );
        }

        var data = null;
        try {
            data = await response.json();
        } catch (parseError) {
            data = null;
        }

        if (!response.ok) {
            throw new Error(data && data.error ? data.error : "The server rejected the request.");
        }
        if (!data) {
            throw new Error("The server returned an unexpected response.");
        }
        return data;
    }

    async function runSimulation() {
        hideError(elements.runError);
        hideNotice();

        if (state.processes.length === 0) {
            showError(
                elements.runError,
                "Add at least one process before running the simulation."
            );
            scrollToElement(document.getElementById("processes"));
            return;
        }

        var quantum = null;
        if (state.selectedAlgorithm === "rr") {
            try {
                quantum = readQuantum();
            } catch (error) {
                showError(elements.runError, error.message);
                return;
            }
        }

        setButtonBusy(elements.runButton, true, "Run simulation", "Running...");

        try {
            var data = await postJSON("/api/schedule", {
                processes: state.processes,
                algorithm: state.selectedAlgorithm,
                quantum: quantum
            });

            state.lastResult = data;
            renderResults(data);
            scrollToElement(document.getElementById("results"));
        } catch (error) {
            showError(elements.runError, error.message);
        } finally {
            setButtonBusy(elements.runButton, false, "Run simulation", "Running...");
        }
    }

    /* ------------------------- Comparison rendering -------------------- */

    function metricCell(result, metricKey, suffix, best) {
        var isBest = Array.isArray(best[metricKey]) && best[metricKey].indexOf(result.algorithm) !== -1;
        return (
            '<td class="num' + (isBest ? " best" : "") + '"' +
            (isBest ? ' title="Best in this metric"' : "") + ">" +
            formatNumber(result.metrics[metricKey], 2) + (suffix || "") +
            "</td>"
        );
    }

    function renderComparison(data) {
        var best = data.best;

        elements.compareBadge.textContent =
            data.process_count + " processes \u00b7 q = " + data.quantum;

        var callouts = [
            { key: "avg_turnaround_time", label: "Lowest avg turnaround", suffix: "" },
            { key: "avg_waiting_time", label: "Lowest avg waiting", suffix: "" },
            { key: "avg_response_time", label: "Lowest avg response", suffix: "" },
            { key: "cpu_utilization", label: "Highest CPU utilization", suffix: "%" }
        ];

        elements.bestCallouts.innerHTML = callouts.map(function (callout) {
            var winners = best[callout.key] || [];
            var winnerResult = data.results.find(function (result) {
                return winners.indexOf(result.algorithm) !== -1;
            });
            var value = winnerResult ? winnerResult.metrics[callout.key] : null;

            return (
                '<div class="best-card">' +
                '<span class="best-label">' + callout.label + "</span>" +
                '<span class="best-value-name">' +
                (winners.length ? escapeHtml(winners.join(" / ")) : "\u2014") +
                "</span>" +
                '<span class="best-number">' + formatNumber(value, 2) + callout.suffix + "</span>" +
                "</div>"
            );
        }).join("");

        elements.compareTbody.innerHTML = data.results.map(function (result) {
            return (
                "<tr>" +
                "<td><strong>" + escapeHtml(result.algorithm) + "</strong>" +
                (result.algorithm_key === "rr" ? ' <span class="tag">q=' + result.quantum + "</span>" : "") +
                "</td>" +
                metricCell(result, "avg_turnaround_time", "", best) +
                metricCell(result, "avg_waiting_time", "", best) +
                metricCell(result, "avg_response_time", "", best) +
                metricCell(result, "cpu_utilization", "%", best) +
                "</tr>"
            );
        }).join("");

        elements.compareEmpty.hidden = true;
        elements.compareContent.hidden = false;

        // Chart.js measures its canvas, so the container must be visible first.
        if (window.ComparisonCharts) {
            window.ComparisonCharts.render(data.results, data.best);
        }
    }

    async function compareAlgorithms() {
        hideError(elements.compareError);
        hideNotice();

        if (state.processes.length === 0) {
            showError(
                elements.compareError,
                "Add at least one process before comparing the algorithms."
            );
            scrollToElement(document.getElementById("processes"));
            return;
        }

        var quantum;
        try {
            quantum = readQuantum();
        } catch (error) {
            showError(
                elements.compareError,
                error.message + " The comparison always includes Round Robin, so a valid quantum is required."
            );
            return;
        }

        setButtonBusy(elements.compareButton, true, "Compare all four", "Comparing...");

        try {
            var data = await postJSON("/api/compare", {
                processes: state.processes,
                quantum: quantum
            });

            state.lastComparison = data;
            renderComparison(data);
            scrollToElement(document.getElementById("compare"));
        } catch (error) {
            showError(elements.compareError, error.message);
        } finally {
            setButtonBusy(elements.compareButton, false, "Compare all four", "Comparing...");
        }
    }

    /* --------------------------- Navigation ---------------------------- */

    function setupScrollSpy() {
        if (!("IntersectionObserver" in window)) {
            return;
        }

        var links = Array.prototype.slice.call(document.querySelectorAll(".nav-link"));
        var sections = links.map(function (link) {
            return document.querySelector(link.getAttribute("href"));
        }).filter(Boolean);

        var observer = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (!entry.isIntersecting) {
                    return;
                }
                links.forEach(function (link) {
                    link.classList.toggle(
                        "active",
                        link.getAttribute("href") === "#" + entry.target.id
                    );
                });
            });
        }, { rootMargin: "-40% 0px -55% 0px", threshold: 0 });

        sections.forEach(function (section) {
            observer.observe(section);
        });
    }

    /* ----------------------------- Wiring ------------------------------ */

    elements.form.addEventListener("submit", handleFormSubmit);

    elements.cancel.addEventListener("click", function () {
        resetForm();
        elements.pid.focus();
    });

    elements.processTbody.addEventListener("click", handleTableClick);
    elements.loadSample.addEventListener("click", loadSample);
    elements.heroSample.addEventListener("click", loadSample);
    elements.clear.addEventListener("click", clearAllProcesses);

    document.querySelectorAll('input[name="algorithm"]').forEach(function (radio) {
        radio.addEventListener("change", function () {
            selectAlgorithm(radio.value);
        });
    });

    elements.quantum.addEventListener("input", invalidateResults);

    [elements.pid, elements.arrival, elements.burst, elements.priority].forEach(function (input) {
        input.addEventListener("input", function () {
            hideError(elements.formError);
        });
    });

    elements.runButton.addEventListener("click", runSimulation);
    elements.compareButton.addEventListener("click", compareAlgorithms);

    renderProcessTable();
    selectAlgorithm("fcfs");
    setupScrollSpy();
})();
