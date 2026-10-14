"""
Unit tests for Leaky Bucket traffic shaping.
"""
import unittest
from algorithms.leaky_bucket import LeakyBucketSimulator


class TestLeakyBucket(unittest.TestCase):

    def test_smooth_traffic(self):
        """Traffic within leak rate should not drop any packets."""
        sim = LeakyBucketSimulator(bucket_capacity=10, leak_rate=3)
        res = sim.simulate(arrival_pattern=[2, 3, 1, 2])
        self.assertEqual(res["summary"]["total_dropped"], 0)
        self.assertEqual(res["summary"]["total_incoming"], 8)
        self.assertEqual(res["summary"]["total_transmitted"], 8)
        self.assertEqual(res["summary"]["loss_percentage"], 0.0)

    def test_burst_overflow(self):
        """Massive burst exceeding capacity drops packets."""
        sim = LeakyBucketSimulator(bucket_capacity=5, leak_rate=2)
        # Bucket starts empty. Time 1: 10 packets arrive.
        # Capacity is 5, so accepted = 5, dropped = 5.
        # Transmitted = 2. Remaining = 3.
        res = sim.simulate(arrival_pattern=[10])
        self.assertGreater(res["summary"]["total_dropped"], 0)
        self.assertEqual(res["summary"]["total_incoming"], 10)
        self.assertEqual(res["steps"][0]["dropped"], 5)
        self.assertEqual(res["steps"][0]["accepted"], 5)
        self.assertEqual(res["steps"][0]["transmitted"], 2)

    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            LeakyBucketSimulator(bucket_capacity=0, leak_rate=2)
        with self.assertRaises(ValueError):
            LeakyBucketSimulator(bucket_capacity=5, leak_rate=0)


if __name__ == "__main__":
    unittest.main()
