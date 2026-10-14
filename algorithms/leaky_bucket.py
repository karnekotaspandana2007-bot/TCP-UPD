"""
Leaky Bucket Algorithm Implementation.

Simulates finite-buffer traffic shaping where packets arrive in irregular bursts
and are dispatched at a constant, uniform output leak rate. If the bucket buffer
overflows, incoming packets are dropped.
"""
from typing import List, Dict, Any


class LeakyBucketSimulator:
    """Discrete-time Leaky Bucket traffic shaper simulator."""

    def __init__(self, bucket_capacity: int, leak_rate: int):
        """
        :param bucket_capacity: Maximum number of packets the bucket queue can hold.
        :param leak_rate: Maximum number of packets transmitted per time slot.
        """
        if bucket_capacity < 1:
            raise ValueError("Bucket capacity must be at least 1")
        if leak_rate < 1:
            raise ValueError("Leak rate must be at least 1")

        self.capacity = int(bucket_capacity)
        self.leak_rate = int(leak_rate)

    def simulate(self, arrival_pattern: List[int]) -> Dict[str, Any]:
        """
        Runs the simulation across a series of time units.
        :param arrival_pattern: List of integer packet arrival counts for each time unit.
        :return: Simulation results with step-by-step trace, metrics, and chart series.
        """
        if not arrival_pattern:
            raise ValueError("Arrival pattern cannot be empty")

        steps: List[Dict[str, Any]] = []
        current_queue = 0
        total_incoming = 0
        total_transmitted = 0
        total_dropped = 0
        max_queue_reached = 0

        # We also drain remaining packets after the input list ends if queue is non-empty
        # up to a reasonable cutoff
        arrivals = list(arrival_pattern)
        # Pad with zeros to allow bucket to leak remaining packets
        drain_steps = 0
        max_drain = 20

        t = 1
        idx = 0
        while idx < len(arrivals) or (current_queue > 0 and drain_steps < max_drain):
            incoming = arrivals[idx] if idx < len(arrivals) else 0
            if idx >= len(arrivals):
                drain_steps += 1
            idx += 1

            total_incoming += incoming
            queue_before_leak = current_queue

            # 1. Enqueue incoming packets into finite buffer
            available_space = self.capacity - current_queue
            if incoming <= available_space:
                accepted = incoming
                dropped = 0
            else:
                accepted = available_space
                dropped = incoming - available_space

            current_queue += accepted
            max_queue_reached = max(max_queue_reached, current_queue)
            total_dropped += dropped

            # 2. Leak / Transmit at fixed rate
            transmitted = min(current_queue, self.leak_rate)
            current_queue -= transmitted
            total_transmitted += transmitted

            utilization_pct = round((current_queue / self.capacity) * 100.0, 1)

            steps.append({
                "time": t,
                "incoming": incoming,
                "accepted": accepted,
                "dropped": dropped,
                "transmitted": transmitted,
                "queue_after_leak": current_queue,
                "capacity": self.capacity,
                "utilization_pct": utilization_pct
            })
            t += 1

        loss_pct = round((total_dropped / total_incoming * 100.0), 2) if total_incoming > 0 else 0.0
        delivery_pct = round((total_transmitted / total_incoming * 100.0), 2) if total_incoming > 0 else 0.0

        return {
            "algorithm": "Leaky Bucket",
            "capacity": self.capacity,
            "leak_rate": self.leak_rate,
            "total_steps": len(steps),
            "summary": {
                "total_incoming": total_incoming,
                "total_transmitted": total_transmitted,
                "total_dropped": total_dropped,
                "max_queue_reached": max_queue_reached,
                "loss_percentage": loss_pct,
                "delivery_percentage": delivery_pct,
                "avg_queue_utilization_pct": round(
                    sum(s["utilization_pct"] for s in steps) / len(steps), 1
                ) if steps else 0.0
            },
            "steps": steps,
            "chart_data": {
                "labels": [f"T={s['time']}" for s in steps],
                "incoming": [s["incoming"] for s in steps],
                "transmitted": [s["transmitted"] for s in steps],
                "dropped": [s["dropped"] for s in steps],
                "queue_size": [s["queue_after_leak"] for s in steps],
                "capacity_line": [self.capacity for _ in steps]
            },
            "explanation": (
                "The Leaky Bucket algorithm models a bucket with a small hole at the bottom. "
                "No matter how bursty water (packets) is poured into the bucket, water leaks out "
                "at a constant, predictable rate. If water is poured in faster than the bucket can hold, "
                "the excess spills over (packet loss). This guarantees a smooth, non-bursty output stream."
            )
        }
