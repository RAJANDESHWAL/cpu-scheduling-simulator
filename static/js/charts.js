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

    var SHORT_LABELS = {
        fcfs: "FCFS",
        sjf: "SJF",
        srtf: "SRTF",
        rr: "RR",
        priority: "Priority",
        priority_preemptive: "Prem. Priority"
    };

    function palette() {
        var dark = document.documentElement.getAttribute("data-theme") === "dark";
        return {
            best: dark ? "#4ade80" : "#15803d",
            bestBorder: dark ? "#86efac" : "#166534",
            normal: dark ? "#2dd4bf" : "#5eead4",
            normalBorder: dark ? "#5eead4" : "#0f766e",
            axisText: dark ? "#cbd5e1" : "#475569",
            tickText: dark ? "#94a3b8" : "#64748b",
            grid: dark ? "#334155" : "#e2e8f0",
            tooltipBackground: dark ? "#e2e8f0" : "#0f172a",
            tooltipTitle: dark ? "#102033" : "#ffffff",
            tooltipBody: dark ? "#334155" : "#e2e8f0"
        };
    }

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

        var colors = palette();
        var backgrounds = algorithms.map(function (name) {
            return isBest(bestList, name) ? colors.best : colors.normal;
        });
        var borders = algorithms.map(function (name) {
            return isBest(bestList, name) ? colors.bestBorder : colors.normalBorder;
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
                        backgroundColor: colors.tooltipBackground,
                        titleColor: colors.tooltipTitle,
                        bodyColor: colors.tooltipBody,
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
                            color: colors.axisText,
                            font: { size: 10.5 },
                            maxRotation: 20,
                            minRotation: 0
                        }
                    },
                    y: {
                        beginAtZero: true,
                        border: { display: false },
                        grid: { color: colors.grid },
                        ticks: {
                            color: colors.tickText,
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
