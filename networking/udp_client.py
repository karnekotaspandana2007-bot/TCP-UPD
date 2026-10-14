"""
UDP Client Experiment Runner.

Transmits independent datagram packets containing sequence numbers and timestamps
to a UDP demonstration server. Uses per-packet socket timeouts to capture lost or
unacknowledged packets, measuring real RTT, delivery ratio, and loss metrics.
"""
import socket
import time
import json
from typing import Dict, Any, List

from analyzer.performance import calculate_metrics


def run_udp_experiment(
    host: str = "127.0.0.1",
    port: int = 5002,
    packet_count: int = 10,
    payload_size: int = 1024,
    interval_ms: float = 0.0,
    timeout_sec: float = 1.0
) -> Dict[str, Any]:
    """
    Executes a real UDP socket experiment.
    """
    packet_count = max(1, min(500, int(packet_count)))
    # Max UDP safe payload size over loopback/Ethernet is 65507 bytes
    payload_size = max(1, min(65507, int(payload_size)))
    interval_sec = max(0.0, float(interval_ms) / 1000.0)
    timeout_sec = max(0.05, min(5.0, float(timeout_sec)))

    dummy_payload = "U" * payload_size
    packet_records: List[Dict[str, Any]] = []
    valid_rtts: List[float] = []
    received_seqs = set()
    duplicate_count = 0
    payload_bytes_received = 0
    missing_seqs: List[int] = []

    client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_sock.settimeout(timeout_sec)

    experiment_start = time.time()

    try:
        for seq in range(1, packet_count + 1):
            msg = {
                "seq": seq,
                "timestamp": time.time(),
                "payload": dummy_payload
            }
            msg_bytes = json.dumps(msg).encode("utf-8")

            t_send = time.time()
            try:
                client_sock.sendto(msg_bytes, (host, int(port)))
            except Exception as e:
                missing_seqs.append(seq)
                packet_records.append({
                    "seq": seq,
                    "size_bytes": payload_size,
                    "sent_time": round(t_send - experiment_start, 4),
                    "ack_time": None,
                    "rtt_ms": None,
                    "status": f"SEND_FAILED: {str(e)}"
                })
                continue

            try:
                ack_bytes, server_addr = client_sock.recvfrom(4096)
                t_ack = time.time()
                ack_data = json.loads(ack_bytes.decode("utf-8"))
                ack_seq = ack_data.get("ack_seq")
                rtt_ms = round((t_ack - t_send) * 1000.0, 3)

                if ack_seq in received_seqs:
                    duplicate_count += 1
                    status = "DUPLICATE_ACK"
                elif ack_seq == seq:
                    received_seqs.add(seq)
                    payload_bytes_received += payload_size
                    valid_rtts.append(rtt_ms)
                    status = "ACKED"
                else:
                    received_seqs.add(ack_seq)
                    status = f"OUT_OF_ORDER (got {ack_seq})"

                packet_records.append({
                    "seq": seq,
                    "size_bytes": payload_size,
                    "sent_time": round(t_send - experiment_start, 4),
                    "ack_time": round(t_ack - experiment_start, 4),
                    "rtt_ms": rtt_ms,
                    "status": status
                })

            except socket.timeout:
                missing_seqs.append(seq)
                packet_records.append({
                    "seq": seq,
                    "size_bytes": payload_size,
                    "sent_time": round(t_send - experiment_start, 4),
                    "ack_time": None,
                    "rtt_ms": None,
                    "status": "TIMEOUT_LOST"
                })
            except Exception as ex:
                missing_seqs.append(seq)
                packet_records.append({
                    "seq": seq,
                    "size_bytes": payload_size,
                    "sent_time": round(t_send - experiment_start, 4),
                    "ack_time": None,
                    "rtt_ms": None,
                    "status": f"ERROR: {str(ex)}"
                })

            if interval_sec > 0 and seq < packet_count:
                time.sleep(interval_sec)

    finally:
        total_elapsed = time.time() - experiment_start
        try:
            client_sock.close()
        except Exception:
            pass

    received_unique = len(received_seqs)

    metrics = calculate_metrics(
        sent_packets=packet_count,
        received_packets=received_unique + duplicate_count,
        received_unique_packets=received_unique,
        payload_bytes_received=payload_bytes_received,
        elapsed_seconds=total_elapsed,
        rtt_list_ms=valid_rtts,
        missing_seqs=missing_seqs,
        duplicate_count=duplicate_count
    )

    return {
        "success": True,
        "protocol": "UDP",
        "host": host,
        "port": port,
        "config": {
            "host": host,
            "port": port,
            "packet_count": packet_count,
            "payload_size": payload_size,
            "interval_ms": interval_ms,
            "timeout_sec": timeout_sec
        },
        "metrics": metrics,
        "packets": packet_records,
        "notes": (
            "UDP is a connectionless, best-effort transport protocol. It does not perform "
            "automatic retransmission or handshaking. Missing packets timed out waiting for server ACK."
        )
    }
