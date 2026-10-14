"""
Integration and functional tests for the Flask REST API.
"""
import unittest
import json
from app import app, tcp_server, udp_server


class TestFlaskAPI(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_health_endpoint(self):
        res = self.app.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")

    def test_servers_status_endpoint(self):
        res = self.app.get("/api/servers/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("tcp", data)
        self.assertIn("udp", data)

    def test_leaky_bucket_api(self):
        payload = {
            "bucket_capacity": 8,
            "leak_rate": 2,
            "arrival_pattern": [4, 6, 2]
        }
        res = self.app.post(
            "/api/leaky-bucket/simulate",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("steps", data)
        self.assertIn("summary", data)

    def test_token_bucket_api(self):
        payload = {
            "bucket_capacity": 10,
            "token_rate": 3,
            "queue_capacity": 5,
            "allow_queueing": True,
            "arrival_pattern": [5, 2, 8]
        }
        res = self.app.post(
            "/api/token-bucket/simulate",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("summary", data)

    def test_congestion_simulation_api(self):
        payload = {
            "mss": 1460,
            "initial_cwnd": 1,
            "initial_ssthresh": 16,
            "total_rounds": 15,
            "timeout_rounds": [8],
            "dup_ack_rounds": []
        }
        res = self.app.post(
            "/api/congestion/simulate",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["rounds_data"]), 15)

    def test_shaping_compare_api(self):
        payload = {
            "capacity": 10,
            "rate": 3,
            "arrival_pattern": [4, 8, 2]
        }
        res = self.app.post(
            "/api/shaping/compare",
            data=json.dumps(payload),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("leaky_bucket", data)
        self.assertIn("token_bucket", data)

    def test_tcp_and_udp_endpoints(self):
        # TCP run
        tcp_res = self.app.post(
            "/api/tcp/start",
            data=json.dumps({"packet_count": 3, "payload_size": 128, "interval_ms": 2}),
            content_type="application/json"
        )
        self.assertEqual(tcp_res.status_code, 200)
        tcp_data = tcp_res.get_json()
        self.assertTrue(tcp_data["success"])

        # UDP run
        udp_res = self.app.post(
            "/api/udp/start",
            data=json.dumps({"packet_count": 3, "payload_size": 128, "interval_ms": 2}),
            content_type="application/json"
        )
        self.assertEqual(udp_res.status_code, 200)
        udp_data = udp_res.get_json()
        self.assertTrue(udp_data["success"])

    def test_comparison_endpoint(self):
        res = self.app.post(
            "/api/compare/run",
            data=json.dumps({"packet_count": 3, "payload_size": 128, "interval_ms": 2}),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("tcp", data)
        self.assertIn("udp", data)

    def test_history_and_dashboard_stats(self):
        # Stats
        stats_res = self.app.get("/api/dashboard/stats")
        self.assertEqual(stats_res.status_code, 200)
        stats = stats_res.get_json()
        self.assertIn("total_experiments", stats)

        # History list
        hist_res = self.app.get("/api/experiments")
        self.assertEqual(hist_res.status_code, 200)
        hist = hist_res.get_json()
        self.assertGreater(hist["count"], 0)

        # Export CSV
        csv_res = self.app.get("/api/experiments/export")
        self.assertEqual(csv_res.status_code, 200)
        self.assertEqual(csv_res.mimetype, "text/csv")
        self.assertIn("Experiment ID", csv_res.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
