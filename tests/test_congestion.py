"""
Unit tests for TCP Congestion Window Simulator.
"""
import unittest
from algorithms.congestion_window import TCPCongestionSimulator


class TestCongestionSimulator(unittest.TestCase):

    def test_slow_start_and_avoidance(self):
        """cwnd doubles in slow start until reaching ssthresh, then grows additively."""
        sim = TCPCongestionSimulator(mss=1460, initial_cwnd=1, initial_ssthresh=8)
        res = sim.simulate(total_rounds=10)
        rounds = res["rounds_data"]

        # Round 1: cwnd=1 (Slow Start)
        self.assertEqual(rounds[0]["cwnd_mss"], 1.0)
        self.assertEqual(rounds[0]["phase"], "Slow Start")

        # Round 2: cwnd=2
        self.assertEqual(rounds[1]["cwnd_mss"], 2.0)

        # Round 3: cwnd=4
        self.assertEqual(rounds[2]["cwnd_mss"], 4.0)

        # Round 4: cwnd=8 (reaches ssthresh=8, next is Congestion Avoidance)
        self.assertEqual(rounds[3]["cwnd_mss"], 8.0)

        # Round 5: in Congestion Avoidance, adds 1 MSS
        self.assertEqual(rounds[4]["cwnd_mss"], 9.0)
        self.assertEqual(rounds[4]["phase"], "Congestion Avoidance")

    def test_timeout_event(self):
        """On timeout, cwnd resets to 1, ssthresh halves."""
        sim = TCPCongestionSimulator(mss=1460, initial_cwnd=1, initial_ssthresh=16)
        # Timeout at round 4
        res = sim.simulate(total_rounds=8, timeout_rounds=[4])
        r4 = res["rounds_data"][3]
        self.assertEqual(r4["event_type"], "TIMEOUT")
        self.assertEqual(r4["cwnd_mss"], 1.0)
        self.assertEqual(r4["phase"], "Slow Start")

    def test_fast_recovery_event(self):
        """On 3 Dup ACKs, cwnd is cut in half without dropping to 1."""
        sim = TCPCongestionSimulator(mss=1460, initial_cwnd=1, initial_ssthresh=16)
        res = sim.simulate(total_rounds=8, dup_ack_rounds=[4])
        r4 = res["rounds_data"][3]
        self.assertEqual(r4["event_type"], "FAST_RECOVERY")
        self.assertGreater(r4["cwnd_mss"], 1.0)
        self.assertEqual(r4["phase"], "Congestion Avoidance")


if __name__ == "__main__":
    unittest.main()
