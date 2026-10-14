"""
TCP Demonstration Server.

Implements a robust, threaded TCP Server using length-prefixed framing:
- Framing: 4-byte big-endian unsigned integer (network byte order '!I')
  followed by UTF-8 encoded JSON payload.
- Avoids partial read and message boundary slicing inherent to raw byte streams.
- Responds to each valid message with an ACK frame containing the sequence number
  and server arrival timestamp.
"""
import socket
import struct
import threading
import json
import time
from typing import Dict, Any, Optional


def send_tcp_frame(sock: socket.socket, data_bytes: bytes) -> None:
    """Send length-prefixed frame over TCP socket."""
    header = struct.pack("!I", len(data_bytes))
    sock.sendall(header + data_bytes)


def recv_exact(sock: socket.socket, num_bytes: int) -> Optional[bytes]:
    """Helper to receive exactly num_bytes from stream."""
    buffer = bytearray()
    while len(buffer) < num_bytes:
        chunk = sock.recv(num_bytes - len(buffer))
        if not chunk:
            return None  # Socket closed
        buffer.extend(chunk)
    return bytes(buffer)


def recv_tcp_frame(sock: socket.socket) -> Optional[bytes]:
    """Receive length-prefixed frame over TCP socket."""
    header = recv_exact(sock, 4)
    if not header or len(header) < 4:
        return None
    length = struct.unpack("!I", header)[0]
    return recv_exact(sock, length)


class TCPServerManager:
    """Manages the lifecycle of a TCP demonstration server."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5001):
        self.host = host
        self.port = int(port)
        self.server_sock: Optional[socket.socket] = None
        self.thread: Optional[threading.Thread] = None
        self.is_running = False
        self._stop_event = threading.Event()
        self.lock = threading.Lock()

        # Stats
        self.stats = {
            "total_connections": 0,
            "messages_received": 0,
            "bytes_received": 0,
            "start_time": None
        }

    def start(self) -> Dict[str, Any]:
        """Start TCP server in background thread."""
        with self.lock:
            if self.is_running:
                return {"status": "ALREADY_RUNNING", "host": self.host, "port": self.port}

            try:
                self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_sock.bind((self.host, self.port))
                self.server_sock.listen(10)
                self.server_sock.settimeout(0.5)  # Periodic timeout to allow checking stop_event

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
        """Main connection acceptance loop."""
        while not self._stop_event.is_set():
            try:
                client_sock, client_addr = self.server_sock.accept()
                self.stats["total_connections"] += 1
                # Handle client in dedicated thread
                t = threading.Thread(target=self._handle_client, args=(client_sock, client_addr), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except Exception:
                if self._stop_event.is_set():
                    break
                time.sleep(0.05)

    def _handle_client(self, client_sock: socket.socket, client_addr) -> None:
        """Handle length-prefixed messages from connected client."""
        client_sock.settimeout(3.0)
        try:
            while not self._stop_event.is_set():
                frame = recv_tcp_frame(client_sock)
                if frame is None:
                    break

                server_now = time.time()
                self.stats["messages_received"] += 1
                self.stats["bytes_received"] += len(frame)

                try:
                    msg = json.loads(frame.decode("utf-8"))
                    seq = msg.get("seq", 0)
                except Exception:
                    seq = -1

                # Send ACK frame
                ack_payload = json.dumps({
                    "ack_seq": seq,
                    "server_time": server_now,
                    "status": "ACK_RECEIVED"
                }).encode("utf-8")
                send_tcp_frame(client_sock, ack_payload)
        except Exception:
            pass
        finally:
            try:
                client_sock.close()
            except Exception:
                pass

    def stop(self) -> Dict[str, Any]:
        """Stop TCP server gracefully."""
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
        """Get current operational status."""
        return {
            "protocol": "TCP",
            "host": self.host,
            "port": self.port,
            "is_running": self.is_running,
            "stats": dict(self.stats)
        }
