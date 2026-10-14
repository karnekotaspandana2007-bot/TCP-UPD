"""
Configuration parameters for TCP/UDP Performance Analyzer
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Network defaults
DEFAULT_HOST = "127.0.0.1"
DEFAULT_TCP_PORT = 5001
DEFAULT_UDP_PORT = 5002

# Limits for safety and stability
MAX_PACKETS = 500
MIN_PACKETS = 1
MAX_PAYLOAD_SIZE = 65507  # Max safe UDP payload size; for TCP we also cap to 65536 for demo
MIN_PAYLOAD_SIZE = 1
DEFAULT_TIMEOUT_SEC = 2.0
MIN_INTERVAL_MS = 0
MAX_INTERVAL_MS = 2000

# Results & Storage
RESULTS_DIR = os.path.join(BASE_DIR, "results")
EXPERIMENTS_FILE = os.path.join(RESULTS_DIR, "experiments.json")

# Ensure results directory exists
os.makedirs(RESULTS_DIR, exist_ok=True)
