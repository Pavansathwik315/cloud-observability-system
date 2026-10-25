import unittest
import tempfile
import sqlite3
import gc
from pathlib import Path

import app as app_module


class ObservabilityTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()

        app_module.DB = (
            Path(cls.temp_dir.name) / "test_observability.db"
        )

        app_module.init_db()

        app_module.app.config["TESTING"] = True
        cls.client = app_module.app.test_client()

    @classmethod
    def tearDownClass(cls):
        # Collect unused objects before cleaning temporary files
        gc.collect()

        # Close any remaining references before cleanup
        cls.temp_dir.cleanup()

    def test_home_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_health_endpoint(self):
        response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get_json()["status"],
            "healthy"
        )

    def test_metrics_endpoint(self):
        response = self.client.get("/api/metrics")

        self.assertEqual(response.status_code, 200)

        data = response.get_json()

        self.assertIn("total_requests", data)
        self.assertIn("alerts", data)

    def test_logs_endpoint(self):
        response = self.client.get("/api/logs")

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.get_json(), list)

    def test_request_is_logged(self):
        self.client.get("/api/health")

        with sqlite3.connect(app_module.DB) as conn:
            count = conn.execute(
                "SELECT COUNT(*) FROM request_logs"
            ).fetchone()[0]

        self.assertGreater(count, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
