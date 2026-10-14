"""
TCP Client Experiment Runner.

Connects to a TCP demonstration server, transmits a stream of length-prefixed
JSON messages with sequence numbers and timestamps, measures round-trip time (RTT)
for each acknowledgement, and calculates accurate performance metrics.
"""
import socket
import time
import json
from typing import Dict, Any, List

from .tcp_server import send_tcp_frame, recv_tcp_frame
from analyzer.performance import calculate_metrics


def run_tcp_experiment(
    host: str = "127.0.0.1",
    port: int = 5001,
    packet_count: int = 10,
    payload_size: int = 1024,
    interval_ms: float = 0.0,
    timeout_sec: float = 2.0
) -> Dict[str, Any]:
    """
    Executes a real TCP socket experiment.
    """
    packet_count = max(1, min(500, int(packet_count)))
    payload_size = max(1, min(65536, int(payload_size)))
    interval_sec = max(0.0, float(interval_ms) / 1000.0)
    timeout_sec = max(0.1, min(10.0, float(timeout_sec)))

    dummy_payload = "X" * payload_size
    packet_records: List[Dict[str, Any]] = []
    valid_rtts: List[float] = []
    received_unique_packets = 0
    payload_bytes_received = 0
    missing_seqs: List[int] = []

    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.settimeout(timeout_sec)

    experiment_start = time.time()
    connected = False

    try:
        client_sock.connect((host, int(port)))
        connected = True
    except ConnectionRefusedError:
        return {
            "success": False,
            "error": f"Connection refused to {host}:{port}. Is the TCP server running?",
            "protocol": "TCP",
            "host": host,
            "port": port
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"TCP Connection error: {str(e)}",
            "protocol": "TCP",
            "host": host,
            "port": port
        }

    try:
        for seq in range(1, packet_count + 1):
            msg = {
                "seq": seq,
                "timestamp": time.time(),
                "payload": dummy_payload
            }
            msg_bytes = json.dumps(msg).encode("utf-8")

            t_send = time.time()
            send_tcp_frame(client_sock, msg_bytes)

            try:
                ack_bytes = recv_tcp_frame(client_sock)
                t_ack = time.time()
                if ack_bytes:
                    ack_data = json.loads(ack_bytes.decode("utf-8"))
                    ack_seq = ack_data.get("ack_seq")
                    rtt_ms = round((t_ack - t_send) * 1000.0, 3)

                    if ack_seq == seq:
                        received_unique_packets += 1
                        payload_bytes_received += payload_size
                        valid_rtts.append(rtt_ms)
                        packet_records.append({
                            "seq": seq,
                            "size_bytes": payload_size,
                            "sent_time": round(t_send - experiment_start, 4),
                            "ack_time": round(t_ack - experiment_start, 4),
                            "rtt_ms": rtt_ms,
                            "status": "ACKED"
                        })
                    else:
                        packet_records.append({
                            "seq": seq,
                            "size_bytes": payload_size,
                            "sent_time": round(t_send - experiment_start, 4),
                            "ack_time": round(t_ack - experiment_start, 4),
                            "rtt_ms": rtt_ms,
                            "status": "MISMATCH_ACK"
                        })
                else:
                    missing_seqs.append(seq)
                    packet_records.append({
                        "seq": seq,
                        "size_bytes": payload_size,
                        "sent_time": round(t_send - experiment_start, 4),
                        "ack_time": None,
                        "rtt_ms": None,
                        "status": "CLOSED"
                    })
            except socket.timeout:
                missing_seqs.append(seq)
                packet_records.append({
                    "seq": seq,
                    "size_bytes": payload_size,
                    "sent_time": round(t_send - experiment_start, 4),
                    "ack_time": None,
                    "rtt_ms": None,
                    "status": "TIMEOUT"
                })

            if interval_sec > 0 and seq < packet_count:
                time.sleep(interval_sec)

    finally:
        total_elapsed = time.time() - experiment_start
        try:
            client_sock.close()
        except Exception:
            pass

    metrics = calculate_metrics(
        sent_packets=packet_count,
        received_packets=received_unique_packets,
        received_unique_packets=received_unique_packets,
        payload_bytes_received=payload_bytes_received,
        elapsed_seconds=total_elapsed,
        rtt_list_ms=valid_rtts,
        missing_seqs=missing_seqs,
        duplicate_count=0
    )

    return {
        "success": True,
        "protocol": "TCP",
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
            "TCP provides reliable, ordered transmission via operating system acknowledgment "
            "and flow control. All packets delivered are confirmed by the application-level server ACK."
        )
    }
