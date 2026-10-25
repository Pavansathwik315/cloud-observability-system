
from flask import Flask, jsonify, request , render_template
import sqlite3
import time
import uuid
from pathlib import Path
from datetime import datetime

app = Flask(__name__)
DB = Path(__file__).with_name("observability.db")


def init_db():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS request_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT,
                timestamp TEXT,
                endpoint TEXT,
                status_code INTEGER,
                latency_ms REAL
            )
        """)


init_db()


@app.before_request
def start_timer():
    request.start_time = time.perf_counter()
    request.request_id = str(uuid.uuid4())


@app.after_request
def record_request(response):
    elapsed = (time.perf_counter() - request.start_time) * 1000

    with sqlite3.connect(DB) as conn:
        conn.execute("""
            INSERT INTO request_logs
            (request_id, timestamp, endpoint, status_code, latency_ms)
            VALUES (?, ?, ?, ?, ?)
        """, (
            request.request_id,
            datetime.now().isoformat(timespec="seconds"),
            request.path,
            response.status_code,
            round(elapsed, 2)
        ))

    response.headers["X-Request-ID"] = request.request_id
    return response


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({
        "service": "order-service",
        "status": "healthy"
    })


@app.route("/api/metrics")
def metrics():
    with sqlite3.connect(DB) as conn:
        rows = conn.execute("""
            SELECT status_code, latency_ms
            FROM request_logs
        """).fetchall()

    total = len(rows)

    failed = sum(
        1 for status, _ in rows if status >= 400
    )

    successful = total - failed

    avg_latency = (
        sum(latency for _, latency in rows) / total
        if total else 0
    )

    # Detect requests taking 1 second or longer
    slow_requests = sum(
        1 for _, latency in rows if latency >= 1000
    )

    error_rate = (
        (failed / total) * 100 if total else 0
    )

    # Generate automatic alerts
    alerts = []

    if failed > 0:
        alerts.append({
            "level": "WARNING",
            "message": f"{failed} failed requests detected"
        })

    if slow_requests > 0:
        alerts.append({
            "level": "WARNING",
            "message": f"{slow_requests} slow requests detected"
        })

    if error_rate >= 10:
        alerts.append({
            "level": "CRITICAL",
            "message": "Error rate has reached 10% or more"
        })

    if not alerts:
        alerts.append({
            "level": "HEALTHY",
            "message": "No alerts. System is healthy."
        })

    return jsonify({
        "total_requests": total,
        "successful_requests": successful,
        "failed_requests": failed,
        "average_latency_ms": round(avg_latency, 2),
        "slow_requests": slow_requests,
        "error_rate_percent": round(error_rate, 2),
        "alerts": alerts
    })


@app.route("/api/logs")
def logs():
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("""
            SELECT * FROM request_logs
            ORDER BY id DESC LIMIT 50
        """).fetchall()

    return jsonify([dict(row) for row in rows])

  
if __name__ == "__main__":
    app.run(debug=True)
