"""
Unit tests for Performance Metrics Calculations.
"""
import unittest
from analyzer.performance import calculate_metrics, PerformanceMetrics


class TestPerformanceMetrics(unittest.TestCase):

    def test_ideal_network(self):
        """10 sent, 10 received, 0 loss, 100% delivery."""
        res = calculate_metrics(
            sent_packets=10,
            received_packets=10,
            received_unique_packets=10,
            payload_bytes_received=10000,
            elapsed_seconds=1.0,
            rtt_list_ms=[10.0, 12.0, 8.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
        )
        self.assertEqual(res["packet_loss_pct"], 0.0)
        self.assertEqual(res["delivery_ratio_pct"], 100.0)
        # 10,000 bytes * 8 / 1s / 1,000,000 = 0.08 Mbps
        self.assertEqual(res["throughput_mbps"], 0.08)
        self.assertEqual(res["avg_rtt_ms"], 10.0)
        self.assertEqual(res["min_rtt_ms"], 8.0)
        self.assertEqual(res["max_rtt_ms"], 12.0)

    def test_lossy_network(self):
        """10 sent, 7 received unique, 3 lost."""
        res = calculate_metrics(
            sent_packets=10,
            received_packets=7,
            received_unique_packets=7,
            payload_bytes_received=7000,
            elapsed_seconds=2.0,
            rtt_list_ms=[20.0, 25.0, 30.0],
            missing_seqs=[3, 6, 9]
        )
        self.assertEqual(res["packet_loss_pct"], 30.0)
        self.assertEqual(res["delivery_ratio_pct"], 70.0)
        self.assertEqual(res["missing_seqs"], [3, 6, 9])

    def test_edge_cases_zero_division(self):
        """Zero packets, zero elapsed time, empty RTT."""
        res = calculate_metrics(
            sent_packets=0,
            received_packets=0,
            received_unique_packets=0,
            payload_bytes_received=0,
            elapsed_seconds=0.0,
            rtt_list_ms=[]
        )
        self.assertEqual(res["packet_loss_pct"], 0.0)
        self.assertEqual(res["delivery_ratio_pct"], 0.0)
        self.assertEqual(res["throughput_mbps"], 0.0)
        self.assertEqual(res["avg_rtt_ms"], 0.0)


if __name__ == "__main__":
    unittest.main()
