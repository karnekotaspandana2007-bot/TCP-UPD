"""
Performance Analysis Engine for Network Experiments.

Calculates real network metrics based on measured round-trip times,
payload size, elapsed wall-clock time, and packet delivery counts.
"""
import math
from typing import List, Dict, Any, Optional


class PerformanceMetrics:
    """Holds calculated network performance metrics."""

    def __init__(
        self,
        sent_packets: int,
        received_packets: int,
        received_unique_packets: int,
        payload_bytes_received: int,
        elapsed_seconds: float,
        rtt_list_ms: List[float],
        missing_seqs: Optional[List[int]] = None,
        duplicate_count: int = 0
    ):
        self.sent_packets = max(0, int(sent_packets))
        self.received_packets = max(0, int(received_packets))
        self.received_unique_packets = max(0, int(received_unique_packets))
        self.payload_bytes_received = max(0, int(payload_bytes_received))
        self.elapsed_seconds = max(0.0, float(elapsed_seconds))
        self.valid_rtts = [rtt for rtt in rtt_list_ms if rtt is not None and rtt >= 0]
        self.missing_seqs = missing_seqs or []
        self.duplicate_count = max(0, int(duplicate_count))

        # Metrics calculation
        self.packet_loss_pct = self._calculate_packet_loss()
        self.delivery_ratio_pct = self._calculate_delivery_ratio()
        self.throughput_mbps = self._calculate_throughput()
        self.avg_rtt_ms = self._calculate_avg_rtt()
        self.min_rtt_ms = min(self.valid_rtts) if self.valid_rtts else 0.0
        self.max_rtt_ms = max(self.valid_rtts) if self.valid_rtts else 0.0
        self.jitter_ms = self._calculate_jitter()

    def _calculate_packet_loss(self) -> float:
        """Packet Loss = ((Sent Packets - Received Unique Packets) / Sent Packets) * 100"""
        if self.sent_packets <= 0:
            return 0.0
        loss = ((self.sent_packets - self.received_unique_packets) / self.sent_packets) * 100.0
        return round(max(0.0, min(100.0, loss)), 2)

    def _calculate_delivery_ratio(self) -> float:
        """Delivery Ratio = (Received Unique Packets / Sent Packets) * 100"""
        if self.sent_packets <= 0:
            return 0.0
        ratio = (self.received_unique_packets / self.sent_packets) * 100.0
        return round(max(0.0, min(100.0, ratio)), 2)

    def _calculate_throughput(self) -> float:
        """Throughput (Mbps) = (Successfully received payload bytes * 8) / elapsed seconds / 1,000,000"""
        if self.elapsed_seconds <= 0.0 or self.payload_bytes_received <= 0:
            return 0.0
        # (bytes * 8 bits/byte) / elapsed_sec / 1,000,000 bits/Mb
        mbps = (self.payload_bytes_received * 8.0) / (self.elapsed_seconds * 1_000_000.0)
        return round(mbps, 4)

    def _calculate_avg_rtt(self) -> float:
        """Average RTT = Sum of valid measured round-trip times / Number of valid measurements"""
        if not self.valid_rtts:
            return 0.0
        return round(sum(self.valid_rtts) / len(self.valid_rtts), 3)

    def _calculate_jitter(self) -> float:
        """Calculates RFC 3550 style inter-arrival jitter / standard deviation of RTT."""
        if len(self.valid_rtts) < 2:
            return 0.0
        mean = sum(self.valid_rtts) / len(self.valid_rtts)
        variance = sum((x - mean) ** 2 for x in self.valid_rtts) / (len(self.valid_rtts) - 1)
        return round(math.sqrt(variance), 3)

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for API response and storage."""
        return {
            "sent_packets": self.sent_packets,
            "received_packets": self.received_packets,
            "received_unique_packets": self.received_unique_packets,
            "missing_seqs": self.missing_seqs,
            "duplicate_count": self.duplicate_count,
            "payload_bytes_received": self.payload_bytes_received,
            "elapsed_seconds": round(self.elapsed_seconds, 4),
            "packet_loss_pct": self.packet_loss_pct,
            "delivery_ratio_pct": self.delivery_ratio_pct,
            "throughput_mbps": self.throughput_mbps,
            "avg_rtt_ms": self.avg_rtt_ms,
            "min_rtt_ms": round(self.min_rtt_ms, 3),
            "max_rtt_ms": round(self.max_rtt_ms, 3),
            "jitter_ms": self.jitter_ms,
            "sample_count": len(self.valid_rtts)
        }


def calculate_metrics(
    sent_packets: int,
    received_packets: int,
    received_unique_packets: int,
    payload_bytes_received: int,
    elapsed_seconds: float,
    rtt_list_ms: List[float],
    missing_seqs: Optional[List[int]] = None,
    duplicate_count: int = 0
) -> Dict[str, Any]:
    """Helper functional wrapper returning dictionary directly."""
    metrics = PerformanceMetrics(
        sent_packets=sent_packets,
        received_packets=received_packets,
        received_unique_packets=received_unique_packets,
        payload_bytes_received=payload_bytes_received,
        elapsed_seconds=elapsed_seconds,
        rtt_list_ms=rtt_list_ms,
        missing_seqs=missing_seqs,
        duplicate_count=duplicate_count
    )
    return metrics.to_dict()
