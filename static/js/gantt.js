/*
 * static/js/gantt.js
 * ------------------
 * Custom Gantt chart renderer (no chart library).
 *
 * Input: an array of timeline blocks produced by the Flask backend:
 *     [{ "pid": "P1", "start": 0, "end": 2 }, ...]
 *
 * The chart is a flex row.  Each block's flex-grow value is its duration, so
 * wider time slices are visibly wider.  A matching flex row below draws the
 * time markers, which keeps labels aligned with block boundaries.
 */
(function () {
    "use strict";

    var IDLE = "Idle";
    var PALETTE = [
        "#0f766e",
        "#1d4ed8",
        "#b45309",
        "#6d28d9",
        "#be123c",
        "#0369a1",
        "#4d7c0f",
        "#a21caf",
        "#475569",
        "#c2410c"
    ];

    var tooltip = null;

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

    function buildColorMap(timeline) {
        var seen = {};
        var pids = [];

        timeline.forEach(function (block) {
            if (block.pid !== IDLE && !seen[block.pid]) {
                seen[block.pid] = true;
                pids.push(block.pid);
            }
        });

        pids.sort(function (a, b) {
            return a.localeCompare(b, undefined, { numeric: true, sensitivity: "base" });
        });

        var colors = {};
        pids.forEach(function (pid, index) {
            colors[pid] = PALETTE[index % PALETTE.length];
        });
        return colors;
    }

    function getTooltip() {
        if (!tooltip) {
            tooltip = document.createElement("div");
            tooltip.className = "gantt-tooltip";
            tooltip.setAttribute("role", "tooltip");
            tooltip.hidden = true;
            document.body.appendChild(tooltip);
        }
        return tooltip;
    }

    function hideTooltip() {
        if (tooltip) {
            tooltip.hidden = true;
        }
    }

    function positionTooltip(x, y) {
        var element = getTooltip();
        var padding = 14;
        var left = x + padding;
        var top = y + padding;
        var rect = element.getBoundingClientRect();

        if (left + rect.width > window.innerWidth - 8) {
            left = x - rect.width - padding;
        }
        if (top + rect.height > window.innerHeight - 8) {
            top = y - rect.height - padding;
        }

        element.style.left = Math.max(8, left) + "px";
        element.style.top = Math.max(8, top) + "px";
    }

    function showTooltip(block, x, y) {
        var element = getTooltip();
        var duration = block.end - block.start;
        var title = block.pid === IDLE ? "CPU idle" : block.pid;

        element.innerHTML =
            "<strong>" + escapeHtml(title) + "</strong>" +
            "<span>Start " + block.start + " &middot; End " + block.end + "</span>" +
            "<span>Duration " + duration + " time unit" + (duration === 1 ? "" : "s") + "</span>";
        element.hidden = false;
        positionTooltip(x, y);
    }

    function createLegendItem(pid, color, isIdle) {
        var item = document.createElement("span");
        item.className = "legend-item";

        var dot = document.createElement("span");
        dot.className = "legend-dot" + (isIdle ? " idle" : "");
        if (color) {
            dot.style.backgroundColor = color;
        }

        var label = document.createElement("span");
        label.textContent = pid;

        item.appendChild(dot);
        item.appendChild(label);
        return item;
    }

    function renderLegend(legendContainer, timeline, colors) {
        legendContainer.innerHTML = "";

        Object.keys(colors).forEach(function (pid) {
            legendContainer.appendChild(createLegendItem(pid, colors[pid], false));
        });

        var hasIdle = timeline.some(function (block) {
            return block.pid === IDLE;
        });
        if (hasIdle) {
            legendContainer.appendChild(createLegendItem("Idle (no process ready)", null, true));
        }
    }

    function render(timeline, container, legendContainer) {
        if (!container) {
            return;
        }

        container.innerHTML = "";
        if (legendContainer) {
            legendContainer.innerHTML = "";
        }

        if (!Array.isArray(timeline) || timeline.length === 0) {
            container.textContent = "No timeline data to display.";
            return;
        }

        var colors = buildColorMap(timeline);
        var scroll = document.createElement("div");
        scroll.className = "gantt-scroll";

        var track = document.createElement("div");
        track.className = "gantt-track";
        track.setAttribute("role", "list");
        track.setAttribute("aria-label", "CPU Gantt chart");

        timeline.forEach(function (block) {
            var duration = block.end - block.start;
            var element = document.createElement("div");
            element.className = "gantt-block" + (block.pid === IDLE ? " idle" : "");
            element.style.flexGrow = String(Math.max(duration, 0.01));
            element.tabIndex = 0;
            element.setAttribute("role", "listitem");
            element.setAttribute(
                "aria-label",
                block.pid + ", start " + block.start + ", end " + block.end +
                ", duration " + duration + " time units"
            );

            if (block.pid !== IDLE) {
                element.style.backgroundColor = colors[block.pid] || "#475569";
            }

            var pidLabel = document.createElement("span");
            pidLabel.className = "gantt-block-pid";
            pidLabel.textContent = block.pid;

            var timeLabel = document.createElement("span");
            timeLabel.className = "gantt-block-time";
            timeLabel.textContent = block.start + "\u2013" + block.end;

            element.appendChild(pidLabel);
            element.appendChild(timeLabel);

            element.addEventListener("mouseenter", function (event) {
                showTooltip(block, event.clientX, event.clientY);
            });
            element.addEventListener("mousemove", function (event) {
                positionTooltip(event.clientX, event.clientY);
            });
            element.addEventListener("mouseleave", hideTooltip);

            element.addEventListener("focus", function () {
                var rect = element.getBoundingClientRect();
                showTooltip(block, rect.left + rect.width / 2, rect.bottom);
            });
            element.addEventListener("blur", hideTooltip);

            track.appendChild(element);
        });

        var axis = document.createElement("div");
        axis.className = "gantt-axis";
        axis.setAttribute("aria-hidden", "true");

        timeline.forEach(function (block, index) {
            var segment = document.createElement("div");
            segment.className = "gantt-axis-seg";
            segment.style.flexGrow = String(Math.max(block.end - block.start, 0.01));

            if (index === timeline.length - 1) {
                var startLabel = document.createElement("span");
                startLabel.textContent = String(block.start);
                var endLabel = document.createElement("span");
                endLabel.textContent = String(block.end);
                segment.appendChild(startLabel);
                segment.appendChild(endLabel);
            } else {
                segment.textContent = String(block.start);
            }

            axis.appendChild(segment);
        });

        scroll.appendChild(track);
        scroll.appendChild(axis);
        container.appendChild(scroll);

        if (legendContainer) {
            renderLegend(legendContainer, timeline, colors);
        }
    }

    // Hide a tooltip that would otherwise float over the page while scrolling.
    window.addEventListener("scroll", hideTooltip, true);
    window.addEventListener("resize", hideTooltip);

    window.GanttChart = { render: render };
})();
