"""
Integration tests for real UDP socket communication.
"""
import unittest
import time
from networking.udp_server import UDPServerManager
from networking.udp_client import run_udp_experiment


class TestUDPIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Use an ephemeral test port
        cls.test_port = 5202
        cls.server = UDPServerManager(host="127.0.0.1", port=cls.test_port)
        start_res = cls.server.start()
        assert start_res["status"] in ["STARTED", "ALREADY_RUNNING"]
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        time.sleep(0.1)

    def test_udp_packet_exchange(self):
        """Verifies 5 UDP packets transmitted, acked, and measured."""
        res = run_udp_experiment(
            host="127.0.0.1",
            port=self.test_port,
            packet_count=5,
            payload_size=256,
            interval_ms=5,
            timeout_sec=1.0
        )
        self.assertTrue(res["success"])
        metrics = res["metrics"]
        self.assertEqual(metrics["sent_packets"], 5)
        self.assertEqual(metrics["received_unique_packets"], 5)
        self.assertEqual(metrics["packet_loss_pct"], 0.0)
        self.assertGreater(metrics["throughput_mbps"], 0.0)

    def test_udp_timeout_unreachable_server(self):
        """When UDP server does not respond, socket timeout captures lost packets."""
        res = run_udp_experiment(
            host="127.0.0.1",
            port=59998,  # Port without server
            packet_count=2,
            payload_size=64,
            timeout_sec=0.2
        )
        self.assertTrue(res["success"])
        metrics = res["metrics"]
        self.assertEqual(metrics["sent_packets"], 2)
        self.assertEqual(metrics["received_unique_packets"], 0)
        self.assertEqual(metrics["packet_loss_pct"], 100.0)
        self.assertEqual(metrics["missing_seqs"], [1, 2])


if __name__ == "__main__":
    unittest.main()
