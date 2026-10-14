"""
Unit tests for Token Bucket algorithm.
"""
import unittest
from algorithms.token_bucket import TokenBucketSimulator


class TestTokenBucket(unittest.TestCase):

    def test_burst_transmission(self):
        """Token bucket allows immediate burst up to capacity."""
        sim = TokenBucketSimulator(bucket_capacity=10, token_rate=2, allow_queueing=True)
        # Bucket starts with 10 tokens.
        # Time 1: 8 packets arrive. Since 10 tokens exist, all 8 transmit in burst!
        res = sim.simulate(arrival_pattern=[8, 0, 0])
        first_step = res["steps"][0]
        self.assertEqual(first_step["incoming"], 8)
        self.assertEqual(first_step["transmitted"], 8)
        self.assertTrue(first_step["is_burst"])
        self.assertEqual(res["summary"]["burst_events"], 1)

    def test_no_queueing_drop(self):
        """When queueing is disabled, packets without tokens are dropped immediately."""
        sim = TokenBucketSimulator(bucket_capacity=3, token_rate=1, allow_queueing=False)
        # 10 packets arrive when max bucket is 3 tokens.
        res = sim.simulate(arrival_pattern=[10])
        first_step = res["steps"][0]
        self.assertEqual(first_step["transmitted"], 3)
        self.assertEqual(first_step["dropped"], 7)


if __name__ == "__main__":
    unittest.main()
