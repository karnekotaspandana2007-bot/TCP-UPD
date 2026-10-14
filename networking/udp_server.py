"""
UDP Demonstration Server.

Implements a datagram socket server that receives UDP packets, decodes sequence numbers,
and transmits acknowledgement datagrams back to the client address.
Supports an optional simulated loss probability for testing loss recovery and timeout handling.
"""
import socket
import threading
import json
import time
import random
from typing import Dict, Any, Optional


class UDPServerManager:
    """Manages the lifecycle of a UDP demonstration server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5002):
        self.host = host
        self.port = int(port)
        self.server_sock: Optional[socket.socket] = None
        self.thread: Optional[threading.Thread] = None
        self.is_running = False
        self._stop_event = threading.Event()
        self.lock = threading.Lock()
        self.simulate_loss_rate = 0.0  # Between 0.0 and 1.0 (0% default)

        # Stats
        self.stats = {
            "packets_received": 0,
            "packets_acked": 0,
            "packets_simulated_dropped": 0,
            "bytes_received": 0,
            "start_time": None
        }

    def set_simulated_loss_rate(self, rate: float) -> None:
        """Sets educational simulated loss rate (0.0 to 0.9)."""
        self.simulate_loss_rate = max(0.0, min(0.9, float(rate)))

    def start(self) -> Dict[str, Any]:
        """Start UDP server in background thread."""
        with self.lock:
            if self.is_running:
                return {"status": "ALREADY_RUNNING", "host": self.host, "port": self.port}

            try:
                self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_sock.bind((self.host, self.port))
                self.server_sock.settimeout(0.5)

                self._stop_event.clear()
                self.is_running = True
                self.stats["start_time"] = time.time()

                self.thread = threading.Thread(target=self._listen_loop, daemon=True)
                self.thread.start()
                return {"status": "STARTED", "host": self.host, "port": self.port}
            except Exception as e:
                self.is_running = False
                if self.server_sock:
                    try:
                        self.server_sock.close()
                    except Exception:
                        pass
                    self.server_sock = None
                return {"status": "ERROR", "error": str(e), "host": self.host, "port": self.port}

    def _listen_loop(self) -> None:
        """Main datagram reception loop."""
        while not self._stop_event.is_set():
            try:
                data, client_addr = self.server_sock.recvfrom(65535)
                self.stats["packets_received"] += 1
                self.stats["bytes_received"] += len(data)

                # Optional simulated packet loss for educational observation
                if self.simulate_loss_rate > 0.0 and random.random() < self.simulate_loss_rate:
                    self.stats["packets_simulated_dropped"] += 1
                    continue

                server_now = time.time()
                try:
                    msg = json.loads(data.decode("utf-8"))
                    seq = msg.get("seq", 0)
                except Exception:
                    seq = -1

                ack_payload = json.dumps({
                    "ack_seq": seq,
                    "server_time": server_now,
                    "status": "ACK_RECEIVED"
                }).encode("utf-8")

                self.server_sock.sendto(ack_payload, client_addr)
                self.stats["packets_acked"] += 1

            except socket.timeout:
                continue
            except Exception:
                if self._stop_event.is_set():
                    break
                time.sleep(0.05)

    def stop(self) -> Dict[str, Any]:
        """Stop UDP server."""
        with self.lock:
            if not self.is_running:
                return {"status": "NOT_RUNNING"}

            self._stop_event.set()
            self.is_running = False
            if self.server_sock:
                try:
                    self.server_sock.close()
                except Exception:
                    pass
                self.server_sock = None

            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=1.0)
                self.thread = None

            return {"status": "STOPPED", "host": self.host, "port": self.port}

    def get_status(self) -> Dict[str, Any]:
        """Get operational status."""
        return {
            "protocol": "UDP",
            "host": self.host,
            "port": self.port,
            "is_running": self.is_running,
            "simulated_loss_rate": self.simulate_loss_rate,
            "stats": dict(self.stats)
        }
