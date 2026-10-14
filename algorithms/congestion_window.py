"""
TCP Congestion-Window Simulator.

Educational simulation of TCP Reno / Tahoe Congestion Control dynamics:
- Slow Start (Exponential growth)
- Congestion Avoidance (Additive Increase / Linear growth)
- Timeout Event (Multiplicative Decrease with drop to 1 MSS)
- Fast Retransmit / Fast Recovery (3 Duplicate ACKs without drop to 1 MSS)

Clearly designated as an educational model, illustrating how TCP dynamically
senses and adapts to network capacity constraints.
"""
from typing import List, Dict, Any, Optional


class TCPCongestionSimulator:
    """Simulates TCP cwnd and ssthresh progression over RTT rounds."""

    def __init__(
        self,
        mss: int = 1460,
        initial_cwnd: int = 1,
        initial_ssthresh: int = 16,
        rtt_duration_ms: float = 50.0
    ):
        """
        :param mss: Maximum Segment Size in bytes.
        :param initial_cwnd: Starting congestion window in MSS units.
        :param initial_ssthresh: Starting slow start threshold in MSS units.
        :param rtt_duration_ms: Nominal simulated round trip time in milliseconds.
        """
        self.mss = max(536, int(mss))
        self.initial_cwnd = max(1, int(initial_cwnd))
        self.initial_ssthresh = max(2, int(initial_ssthresh))
        self.rtt_duration_ms = max(1.0, float(rtt_duration_ms))

    def simulate(
        self,
        total_rounds: int = 25,
        timeout_rounds: Optional[List[int]] = None,
        dup_ack_rounds: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Simulate cwnd over rounds.
        :param total_rounds: Number of RTT rounds to simulate.
        :param timeout_rounds: List of round numbers where packet loss/timeout occurs.
        :param dup_ack_rounds: List of round numbers where 3-duplicate ACKs occur.
        """
        total_rounds = max(5, min(100, int(total_rounds)))
        timeout_set = set(timeout_rounds or [])
        dup_ack_set = set(dup_ack_rounds or [])

        cwnd = float(self.initial_cwnd)
        ssthresh = float(self.initial_ssthresh)
        phase = "Slow Start"

        records: List[Dict[str, Any]] = []
        events_log: List[Dict[str, Any]] = []

        for r in range(1, total_rounds + 1):
            rtt_timestamp_ms = round(r * self.rtt_duration_ms, 1)
            bytes_in_flight = int(cwnd * self.mss)
            start_cwnd = cwnd
            start_ssthresh = ssthresh
            event_type = "NORMAL"
            event_desc = ""

            # Check for congestion events at this round
            if r in timeout_set:
                event_type = "TIMEOUT"
                old_cwnd = cwnd
                ssthresh = max(2.0, cwnd / 2.0)
                cwnd = 1.0
                phase = "Slow Start"
                event_desc = (
                    f"Round {r}: Simulated Packet Loss / Retransmission Timeout! "
                    f"ssthresh reduced from {start_ssthresh:.1f} to {ssthresh:.1f} (half of cwnd={old_cwnd:.1f}). "
                    f"cwnd reset to 1 MSS ({self.mss} bytes). Entering Slow Start."
                )
                events_log.append({
                    "round": r,
                    "event": "Timeout",
                    "description": event_desc,
                    "severity": "high"
                })
            elif r in dup_ack_set:
                event_type = "FAST_RECOVERY"
                old_cwnd = cwnd
                ssthresh = max(2.0, cwnd / 2.0)
                # Reno Fast Recovery: set cwnd to ssthresh (skips drop to 1)
                cwnd = ssthresh
                phase = "Congestion Avoidance"
                event_desc = (
                    f"Round {r}: 3 Duplicate ACKs received (Fast Retransmit & Recovery)! "
                    f"Packet loss detected early without timer expiration. "
                    f"ssthresh set to {ssthresh:.1f}, cwnd set to {cwnd:.1f} MSS. "
                    f"Resuming in Congestion Avoidance directly."
                )
                events_log.append({
                    "round": r,
                    "event": "3 Duplicate ACKs",
                    "description": event_desc,
                    "severity": "medium"
                })
            else:
                # Normal ACK progression
                if cwnd < ssthresh:
                    phase = "Slow Start"
                    event_desc = (
                        f"Round {r}: Slow Start phase. cwnd={start_cwnd:.1f} < ssthresh={start_ssthresh:.1f}. "
                        f"Window increases exponentially (+1 MSS per successful ACK, doubling window)."
                    )
                    # Next round window will double, bounded if passing ssthresh
                    next_cwnd = cwnd * 2.0
                else:
                    phase = "Congestion Avoidance"
                    event_desc = (
                        f"Round {r}: Congestion Avoidance phase. cwnd={start_cwnd:.1f} >= ssthresh={start_ssthresh:.1f}. "
                        f"Window increases additively (+1 MSS per RTT) to probe bandwidth gently."
                    )
                    next_cwnd = cwnd + 1.0

            # Record round state
            records.append({
                "round": r,
                "rtt_ms": rtt_timestamp_ms,
                "cwnd_mss": round(cwnd, 2),
                "cwnd_bytes": int(cwnd * self.mss),
                "ssthresh_mss": round(ssthresh, 2),
                "phase": phase,
                "event_type": event_type,
                "description": event_desc
            })

            # Update for next iteration if not already an event round
            if event_type == "NORMAL":
                cwnd = next_cwnd

        return {
            "simulator_name": "TCP Reno Educational Congestion Control Simulator",
            "mss_bytes": self.mss,
            "initial_ssthresh": self.initial_ssthresh,
            "total_rounds": total_rounds,
            "summary": {
                "max_cwnd_mss": max(rec["cwnd_mss"] for rec in records),
                "final_cwnd_mss": records[-1]["cwnd_mss"],
                "final_ssthresh_mss": records[-1]["ssthresh_mss"],
                "final_phase": records[-1]["phase"],
                "total_events": len(events_log)
            },
            "events_log": events_log,
            "rounds_data": records,
            "chart_data": {
                "rounds": [f"RTT {r['round']}" for r in records],
                "cwnd": [r["cwnd_mss"] for r in records],
                "ssthresh": [r["ssthresh_mss"] for r in records],
                "phases": [r["phase"] for r in records]
            },
            "educational_notes": {
                "slow_start": (
                    "In Slow Start, cwnd starts small (1 MSS) and doubles every RTT. "
                    "Despite its name, growth is exponential and quickly ramps up throughput."
                ),
                "congestion_avoidance": (
                    "When cwnd reaches ssthresh, TCP switches to Additive Increase. "
                    "cwnd grows linearly (+1 MSS per RTT), probing link capacity safely."
                ),
                "timeout_vs_dup_ack": (
                    "A Timeout indicates severe congestion or lost ACKs; cwnd crashes to 1. "
                    "In contrast, 3 Duplicate ACKs indicate partial network flow; Fast Retransmit / "
                    "Fast Recovery cuts cwnd in half and continues linearly, saving substantial time."
                ),
                "modern_variants": (
                    "Modern OS TCP stacks often use TCP CUBIC (uses a cubic polynomial window function) "
                    "or Google BBR (Bottleneck Bandwidth and RTT model based on packet pacing rather than loss)."
                )
            }
        }
