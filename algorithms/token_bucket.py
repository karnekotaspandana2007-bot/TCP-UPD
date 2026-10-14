"""
Token Bucket Algorithm Implementation.

Simulates traffic shaping/policing using tokens. Tokens are continuously
generated at a constant rate into a bucket of fixed capacity. Packets are
transmitted immediately if sufficient tokens exist, allowing controlled bursts
up to bucket capacity. If tokens are insufficient, packets are queued or dropped.
"""
from typing import List, Dict, Any, Optional


class TokenBucketSimulator:
    """Discrete-time Token Bucket traffic shaper simulator."""

    def __init__(
        self,
        bucket_capacity: int,
        token_rate: int,
        queue_capacity: int = 10,
        allow_queueing: bool = True
    ):
        """
        :param bucket_capacity: Maximum number of tokens the bucket can hold.
        :param token_rate: Number of tokens added per time slot.
        :param queue_capacity: Maximum packet buffer size when queueing is enabled.
        :param allow_queueing: If True, excess packets are queued; if False, dropped.
        """
        if bucket_capacity < 1:
            raise ValueError("Token bucket capacity must be at least 1")
        if token_rate < 1:
            raise ValueError("Token generation rate must be at least 1")

        self.capacity = int(bucket_capacity)
        self.token_rate = int(token_rate)
        self.queue_capacity = int(queue_capacity)
        self.allow_queueing = bool(allow_queueing)

    def simulate(self, arrival_pattern: List[int], token_cost_per_packet: int = 1) -> Dict[str, Any]:
        """
        Simulate Token Bucket processing.
        :param arrival_pattern: List of packet counts arriving at each time step.
        :param token_cost_per_packet: Tokens required per packet (default 1).
        """
        if not arrival_pattern:
            raise ValueError("Arrival pattern cannot be empty")

        steps: List[Dict[str, Any]] = []
        tokens = self.capacity  # Initially starts with full bucket of tokens
        packet_queue = 0
        total_incoming = 0
        total_transmitted = 0
        total_dropped = 0
        burst_events = 0
        max_burst_size = 0

        arrivals = list(arrival_pattern)
        max_drain = 20
        drain_steps = 0

        t = 1
        idx = 0
        while idx < len(arrivals) or (packet_queue > 0 and drain_steps < max_drain):
            incoming = arrivals[idx] if idx < len(arrivals) else 0
            if idx >= len(arrivals):
                drain_steps += 1
            idx += 1

            total_incoming += incoming
            tokens_before_add = tokens

            # 1. Replenish tokens up to capacity
            tokens = min(self.capacity, tokens + self.token_rate)
            tokens_available = tokens

            # 2. Arriving packets handling
            dropped = 0
            eligible_packets = incoming + packet_queue

            if self.allow_queueing:
                # Excess over queue capacity dropped
                if incoming + packet_queue > self.queue_capacity:
                    over = (incoming + packet_queue) - self.queue_capacity
                    dropped = over
                    eligible_packets = self.queue_capacity
            else:
                # Without queueing, packets that cannot be served with available tokens will drop
                pass

            total_dropped += dropped

            # 3. Transmit packets as long as tokens are available
            max_can_send = tokens // token_cost_per_packet
            packets_to_send = min(eligible_packets, max_can_send)
            tokens_used = packets_to_send * token_cost_per_packet
            tokens -= tokens_used

            if self.allow_queueing:
                packet_queue = eligible_packets - packets_to_send
            else:
                dropped_unserved = eligible_packets - packets_to_send
                dropped += dropped_unserved
                total_dropped += dropped_unserved
                packet_queue = 0

            total_transmitted += packets_to_send

            # Check if this step was a burst (> token_rate packets transmitted)
            if packets_to_send > self.token_rate:
                burst_events += 1
                max_burst_size = max(max_burst_size, packets_to_send)

            steps.append({
                "time": t,
                "incoming": incoming,
                "tokens_available": tokens_available,
                "transmitted": packets_to_send,
                "tokens_consumed": tokens_used,
                "tokens_remaining": tokens,
                "queue_size": packet_queue,
                "dropped": dropped,
                "is_burst": packets_to_send > self.token_rate
            })
            t += 1

        loss_pct = round((total_dropped / total_incoming * 100.0), 2) if total_incoming > 0 else 0.0
        delivery_pct = round((total_transmitted / total_incoming * 100.0), 2) if total_incoming > 0 else 0.0

        return {
            "algorithm": "Token Bucket",
            "capacity": self.capacity,
            "token_rate": self.token_rate,
            "allow_queueing": self.allow_queueing,
            "queue_capacity": self.queue_capacity,
            "total_steps": len(steps),
            "summary": {
                "total_incoming": total_incoming,
                "total_transmitted": total_transmitted,
                "total_dropped": total_dropped,
                "burst_events": burst_events,
                "max_burst_size": max_burst_size,
                "loss_percentage": loss_pct,
                "delivery_percentage": delivery_pct,
                "avg_tokens_remaining": round(
                    sum(s["tokens_remaining"] for s in steps) / len(steps), 1
                ) if steps else 0.0
            },
            "steps": steps,
            "chart_data": {
                "labels": [f"T={s['time']}" for s in steps],
                "incoming": [s["incoming"] for s in steps],
                "transmitted": [s["transmitted"] for s in steps],
                "tokens_remaining": [s["tokens_remaining"] for s in steps],
                "queue_size": [s["queue_size"] for s in steps],
                "dropped": [s["dropped"] for s in steps]
            },
            "explanation": (
                "The Token Bucket algorithm accumulates tokens at a fixed rate up to a maximum bucket capacity. "
                "Unlike Leaky Bucket which forces a strictly constant output rate, Token Bucket allows short bursts "
                "of traffic to transmit immediately as long as tokens are available in the bucket. Once tokens are "
                "exhausted, transmissions are bounded by the token generation rate."
            )
        }
