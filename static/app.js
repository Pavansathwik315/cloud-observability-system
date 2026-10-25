const totalRequests = document.getElementById("total-requests");
const successfulRequests = document.getElementById("successful-requests");
const failedRequests = document.getElementById("failed-requests");
const averageLatency = document.getElementById("average-latency");
const logsTable = document.getElementById("logs-table");

let requestChart = null;

function formatRequestId(id) {
    return id ? id.substring(0, 8) + "..." : "N/A";
}

async function loadMetrics() {
    try {
        const response = await fetch("/api/metrics");

        if (!response.ok) {
            throw new Error("Could not load metrics");
        }

        const data = await response.json();

        totalRequests.textContent = data.total_requests;
        successfulRequests.textContent = data.successful_requests;
        failedRequests.textContent = data.failed_requests;
        averageLatency.textContent = Number(
            data.average_latency_ms
        ).toFixed(2);

        updateChart(
            data.successful_requests,
            data.failed_requests
        );
    } catch (error) {
        console.error("Metrics error:", error);
    }
}

function updateChart(successful, failed) {
    const canvas = document.getElementById("requestChart");

    if (!canvas || typeof Chart === "undefined") {
        return;
    }

    if (!requestChart) {
        requestChart = new Chart(canvas, {
            type: "bar",
            data: {
                labels: ["Successful Requests", "Failed Requests"],
                datasets: [{
                    label: "Number of Requests",
                    data: [successful, failed],
                    backgroundColor: ["#22c55e", "#ef4444"],
                    borderRadius: 8,
                    maxBarThickness: 100
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            color: "#cbd5e1"
                        },
                        grid: {
                            color: "#263247"
                        }
                    },
                    x: {
                        ticks: {
                            color: "#cbd5e1"
                        },
                        grid: {
                            display: false
                        }
                    }
                },
                plugins: {
                    legend: {
                        labels: {
                            color: "#e5e7eb"
                        }
                    }
                }
            }
        });
    } else {
        requestChart.data.datasets[0].data = [successful, failed];
        requestChart.update();
    }
}

async function loadLogs() {
    try {
        const response = await fetch("/api/logs");

        if (!response.ok) {
            throw new Error("Could not load logs");
        }

        const logs = await response.json();

        logsTable.replaceChildren();

        if (logs.length === 0) {
            const row = logsTable.insertRow();
            const cell = row.insertCell();
            cell.colSpan = 5;
            cell.textContent = "No requests recorded yet.";
            return;
        }

        logs.forEach(log => {
            const row = logsTable.insertRow();

            const values = [
                formatRequestId(log.request_id),
                log.timestamp,
                log.endpoint,
                log.status_code,
                Number(log.latency_ms).toFixed(2) + " ms"
            ];

            values.forEach((value, index) => {
                const cell = row.insertCell();
                cell.textContent = value;

                if (index === 3) {
                    cell.className =
                        Number(log.status_code) >= 400
                            ? "failure"
                            : "success";
                }
            });
        });
    } catch (error) {
        console.error("Logs error:", error);
    }
}

async function refreshDashboard() {
    await Promise.all([loadMetrics(), loadLogs()]);
}

refreshDashboard();
setInterval(refreshDashboard, 5000);
