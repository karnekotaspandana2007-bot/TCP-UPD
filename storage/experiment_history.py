"""
Experiment History Storage.
Manages reading, writing, filtering, and CSV export of experiments.
"""
import os
import json
import csv
import io
import time
import uuid
from datetime import datetime
from threading import Lock
from typing import List, Dict, Any, Optional

from config import EXPERIMENTS_FILE, RESULTS_DIR


class ExperimentStorage:
    """Thread-safe JSON-backed storage for experiment runs."""

    def __init__(self, file_path: str = EXPERIMENTS_FILE):
        self.file_path = file_path
        self._lock = Lock()
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)

    def _read_all_unlocked(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.file_path):
            return []
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _write_all_unlocked(self, data: List[Dict[str, Any]]) -> None:
        temp_file = f"{self.file_path}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_file, self.file_path)

    def save_experiment(
        self,
        exp_type: str,
        category: str,  # 'REAL_NETWORK' or 'SIMULATION'
        config_params: Dict[str, Any],
        metrics: Dict[str, Any],
        status: str = "SUCCESS",
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Save a new experiment run."""
        with self._lock:
            records = self._read_all_unlocked()
            exp_id = f"EXP-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
            record = {
                "id": exp_id,
                "timestamp": datetime.now().isoformat(),
                "readable_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "type": exp_type,
                "category": category,
                "config": config_params,
                "metrics": metrics,
                "status": status,
                "details": details or {}
            }
            # Prepend newest first
            records.insert(0, record)
            # Limit history to 100 entries to prevent runaway file size
            if len(records) > 100:
                records = records[:100]
            self._write_all_unlocked(records)
            return record

    def get_all(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Return all experiments, newest first."""
        with self._lock:
            records = self._read_all_unlocked()
            return records[:limit]

    def get_by_id(self, exp_id: str) -> Optional[Dict[str, Any]]:
        """Get experiment by ID."""
        with self._lock:
            for item in self._read_all_unlocked():
                if item.get("id") == exp_id:
                    return item
            return None

    def clear(self) -> bool:
        """Clear all experiment history."""
        with self._lock:
            self._write_all_unlocked([])
            return True

    def export_csv(self) -> str:
        """Export history records as CSV string."""
        with self._lock:
            records = self._read_all_unlocked()

        output = io.StringIO()
        writer = csv.writer(output)
        # Header
        writer.writerow([
            "Experiment ID",
            "Timestamp",
            "Type",
            "Category",
            "Status",
            "Packets Sent",
            "Packets Received",
            "Packet Loss (%)",
            "Delivery Ratio (%)",
            "Avg Latency (ms)",
            "Throughput (Mbps)",
            "Elapsed Time (s)",
            "Configuration Summary"
        ])

        for r in records:
            m = r.get("metrics", {})
            cfg = r.get("config", {})
            cfg_summary = "; ".join(f"{k}={v}" for k, v in cfg.items() if k not in ["payload_data"])
            writer.writerow([
                r.get("id", ""),
                r.get("readable_time", r.get("timestamp", "")),
                r.get("type", ""),
                r.get("category", ""),
                r.get("status", ""),
                m.get("sent_packets", m.get("total_packets", 0)),
                m.get("received_unique_packets", m.get("received_packets", m.get("transmitted_packets", 0))),
                m.get("packet_loss_pct", m.get("loss_pct", 0.0)),
                m.get("delivery_ratio_pct", 0.0),
                m.get("avg_rtt_ms", 0.0),
                m.get("throughput_mbps", 0.0),
                m.get("elapsed_seconds", 0.0),
                cfg_summary
            ])

        return output.getvalue()

    def get_summary_stats(self) -> Dict[str, Any]:
        """Aggregate stats across experiments for dashboard cards."""
        with self._lock:
            records = self._read_all_unlocked()

        total_experiments = len(records)
        real_records = [r for r in records if r.get("category") == "REAL_NETWORK"]

        total_sent = 0
        total_recv = 0
        rtts = []
        throughputs = []
        latest_status = "IDLE"
        latest_type = "None"

        if records:
            latest = records[0]
            latest_status = latest.get("status", "SUCCESS")
            latest_type = latest.get("type", "None")

        for r in real_records:
            m = r.get("metrics", {})
            total_sent += m.get("sent_packets", 0)
            total_recv += m.get("received_unique_packets", m.get("received_packets", 0))
            if m.get("avg_rtt_ms", 0) > 0:
                rtts.append(m.get("avg_rtt_ms"))
            if m.get("throughput_mbps", 0) > 0:
                throughputs.append(m.get("throughput_mbps"))

        overall_loss_pct = 0.0
        if total_sent > 0:
            overall_loss_pct = round(((total_sent - total_recv) / total_sent) * 100.0, 2)

        avg_latency = round(sum(rtts) / len(rtts), 2) if rtts else 0.0
        avg_throughput = round(sum(throughputs) / len(throughputs), 3) if throughputs else 0.0

        return {
            "total_experiments": total_experiments,
            "real_experiments_count": len(real_records),
            "total_packets_sent": total_sent,
            "total_packets_received": total_recv,
            "overall_packet_loss_pct": max(0.0, overall_loss_pct),
            "overall_avg_latency_ms": avg_latency,
            "overall_avg_throughput_mbps": avg_throughput,
            "latest_experiment_status": latest_status,
            "latest_experiment_type": latest_type,
            "has_data": total_experiments > 0
        }
