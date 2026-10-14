"""
Integration tests for real TCP socket communication.
"""
import unittest
import time
from networking.tcp_server import TCPServerManager
from networking.tcp_client import run_tcp_experiment


class TestTCPIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Use an ephemeral test port
        cls.test_port = 5201
        cls.server = TCPServerManager(host="127.0.0.1", port=cls.test_port)
        start_res = cls.server.start()
        assert start_res["status"] in ["STARTED", "ALREADY_RUNNING"]
        time.sleep(0.1)  # Allow bind to settle

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        time.sleep(0.1)

    def test_tcp_packet_exchange(self):
        """Verifies 5 packets sent, delivered, acked, and measured."""
        res = run_tcp_experiment(
            host="127.0.0.1",
            port=self.test_port,
            packet_count=5,
            payload_size=256,
            interval_ms=5,
            timeout_sec=1.5
        )
        self.assertTrue(res["success"])
        metrics = res["metrics"]
        self.assertEqual(metrics["sent_packets"], 5)
        self.assertEqual(metrics["received_unique_packets"], 5)
        self.assertEqual(metrics["packet_loss_pct"], 0.0)
        self.assertEqual(metrics["delivery_ratio_pct"], 100.0)
        self.assertGreater(metrics["throughput_mbps"], 0.0)
        self.assertGreater(len(res["packets"]), 0)

    def test_tcp_connection_refused(self):
        """Attempts connection to a closed port and expects safe failure."""
        res = run_tcp_experiment(
            host="127.0.0.1",
            port=59999,  # Unused port
            packet_count=1,
            payload_size=64,
            timeout_sec=0.5
        )
        self.assertFalse(res["success"])
        self.assertIn("error", res)


if __name__ == "__main__":
    unittest.main()
