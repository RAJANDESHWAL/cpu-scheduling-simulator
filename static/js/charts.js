/*
 * static/js/charts.js
 * -------------------
 * Chart.js bar charts for the algorithm comparison.
 *
 * Chart.js itself is loaded from a CDN in index.html.  If the CDN is not
 * reachable, this file shows a readable fallback instead of crashing.
 */
(function () {
    "use strict";

    var charts = {};

    var BEST_COLOR = "#15803d";
    var BEST_BORDER = "#166534";
    var NORMAL_COLOR = "#5eead4";
    var NORMAL_BORDER = "#0f766e";
    var SHORT_LABELS = {
        fcfs: "FCFS",
        sjf: "SJF",
        srtf: "SRTF",
        rr: "RR",
        priority: "Priority"
    };

    function isBest(bestList, algorithmName) {
        return Array.isArray(bestList) && bestList.indexOf(algorithmName) !== -1;
    }

    function showFallback() {
        document.querySelectorAll(".chart-box").forEach(function (box) {
            var message = document.createElement("p");
            message.className = "chart-fallback";
            message.textContent =
                "Chart.js could not be loaded from the CDN. Check your internet connection and reload the page. " +
                "The comparison table above still contains every value.";
            box.replaceChildren(message);
        });
    }

    function destroyCharts() {
        Object.keys(charts).forEach(function (key) {
            if (charts[key]) {
                charts[key].destroy();
            }
        });
        charts = {};
    }

    function makeChart(canvasId, key, labels, values, bestList, algorithms, metricLabel, suffix) {
        var canvas = document.getElementById(canvasId);
        if (!canvas) {
            return;
        }

        var backgrounds = algorithms.map(function (name) {
            return isBest(bestList, name) ? BEST_COLOR : NORMAL_COLOR;
        });
        var borders = algorithms.map(function (name) {
            return isBest(bestList, name) ? BEST_BORDER : NORMAL_BORDER;
        });

        charts[key] = new Chart(canvas.getContext("2d"), {
            type: "bar",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: metricLabel,
                        data: values,
                        backgroundColor: backgrounds,
                        borderColor: borders,
                        borderWidth: 1,
                        borderRadius: 6,
                        maxBarThickness: 54
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return metricLabel + ": " + Number(context.parsed.y).toFixed(2) + suffix;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            color: "#475569",
                            font: { size: 10.5 },
                            maxRotation: 20,
                            minRotation: 0
                        }
                    },
                    y: {
                        beginAtZero: true,
                        border: { display: false },
                        grid: { color: "#e2e8f0" },
                        ticks: {
                            color: "#64748b",
                            font: { size: 10 },
                            callback: function (value) {
                                return value + suffix;
                            }
                        }
                    }
                }
            }
        });
    }

    function render(results, best) {
        if (typeof Chart === "undefined") {
            showFallback();
            return;
        }

        destroyCharts();

        var labels = results.map(function (result) {
            var shortLabel = SHORT_LABELS[result.algorithm_key] || result.algorithm;
            if (result.algorithm_key === "rr") {
                return shortLabel + " (q=" + result.quantum + ")";
            }
            return shortLabel;
        });
        var algorithms = results.map(function (result) {
            return result.algorithm;
        });

        makeChart(
            "chart-wt",
            "wt",
            labels,
            results.map(function (result) { return result.metrics.avg_waiting_time; }),
            best.avg_waiting_time,
            algorithms,
            "Avg waiting time",
            ""
        );

        makeChart(
            "chart-tat",
            "tat",
            labels,
            results.map(function (result) { return result.metrics.avg_turnaround_time; }),
            best.avg_turnaround_time,
            algorithms,
            "Avg turnaround time",
            ""
        );

        makeChart(
            "chart-rt",
            "rt",
            labels,
            results.map(function (result) { return result.metrics.avg_response_time; }),
            best.avg_response_time,
            algorithms,
            "Avg response time",
            ""
        );
    }

    window.ComparisonCharts = { render: render };
})();
