"""
TCP/UDP Client-Server Communication and Performance Analyzer
Flask Backend Application
"""
import os
import sys
import json
from flask import Flask, render_template, request, jsonify, Response

from config import (
    DEFAULT_HOST,
    DEFAULT_TCP_PORT,
    DEFAULT_UDP_PORT,
    MAX_PACKETS,
    MIN_PACKETS,
    MAX_PAYLOAD_SIZE,
    MIN_PAYLOAD_SIZE,
    DEFAULT_TIMEOUT_SEC,
    RESULTS_DIR
)
from networking.tcp_server import TCPServerManager
from networking.tcp_client import run_tcp_experiment
from networking.udp_server import UDPServerManager
from networking.udp_client import run_udp_experiment
from algorithms.leaky_bucket import LeakyBucketSimulator
from algorithms.token_bucket import TokenBucketSimulator
from algorithms.congestion_window import TCPCongestionSimulator
from storage.experiment_history import ExperimentStorage

app = Flask(__name__, static_folder="static", template_folder="templates")

# Initialize storage
storage = ExperimentStorage()

# Initialize background demonstration server managers
tcp_server = TCPServerManager(host=DEFAULT_HOST, port=DEFAULT_TCP_PORT)
udp_server = UDPServerManager(host=DEFAULT_HOST, port=DEFAULT_UDP_PORT)

# Auto-start demo servers on launch for immediate out-of-the-box readiness
tcp_server.start()
udp_server.start()


@app.route("/")
def index():
    """Renders the main dashboard interface."""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "TCP/UDP Performance Analyzer",
        "version": "1.0.0",
        "python_version": sys.version.split()[0]
    })


@app.route("/api/servers/status", methods=["GET"])
def servers_status():
    """Returns real-time status of TCP and UDP demonstration servers."""
    return jsonify({
        "tcp": tcp_server.get_status(),
        "udp": udp_server.get_status()
    })


@app.route("/api/servers/tcp/start", methods=["POST"])
def start_tcp_server_endpoint():
    data = request.get_json(silent=True) or {}
    port = int(data.get("port", DEFAULT_TCP_PORT))
    if port != tcp_server.port:
        tcp_server.stop()
        tcp_server.port = port
    res = tcp_server.start()
    return jsonify(res)


@app.route("/api/servers/tcp/stop", methods=["POST"])
def stop_tcp_server_endpoint():
    res = tcp_server.stop()
    return jsonify(res)


@app.route("/api/servers/udp/start", methods=["POST"])
def start_udp_server_endpoint():
    data = request.get_json(silent=True) or {}
    port = int(data.get("port", DEFAULT_UDP_PORT))
    sim_loss = float(data.get("simulate_loss_rate", 0.0))
    if port != udp_server.port:
        udp_server.stop()
        udp_server.port = port
    udp_server.set_simulated_loss_rate(sim_loss)
    res = udp_server.start()
    return jsonify(res)


@app.route("/api/servers/udp/stop", methods=["POST"])
def stop_udp_server_endpoint():
    res = udp_server.stop()
    return jsonify(res)


@app.route("/api/tcp/start", methods=["POST"])
def start_tcp_experiment():
    """Run real TCP socket experiment."""
    data = request.get_json(silent=True) or {}
    host = data.get("host", DEFAULT_HOST).strip()
    try:
        port = int(data.get("port", DEFAULT_TCP_PORT))
        packet_count = int(data.get("packet_count", 10))
        payload_size = int(data.get("payload_size", 1024))
        interval_ms = float(data.get("interval_ms", 0.0))
        timeout_sec = float(data.get("timeout_sec", DEFAULT_TIMEOUT_SEC))
    except (ValueError, TypeError) as e:
        return jsonify({"success": False, "error": f"Invalid numerical parameters: {str(e)}"}), 400

    # Validation
    if packet_count < MIN_PACKETS or packet_count > MAX_PACKETS:
        return jsonify({"success": False, "error": f"Packet count must be between {MIN_PACKETS} and {MAX_PACKETS}"}), 400
    if payload_size < MIN_PAYLOAD_SIZE or payload_size > MAX_PAYLOAD_SIZE:
        return jsonify({"success": False, "error": f"Payload size must be between {MIN_PAYLOAD_SIZE} and {MAX_PAYLOAD_SIZE} bytes"}), 400

    # Ensure demo server is active if targeted at localhost default port
    if host in ["127.0.0.1", "localhost"] and port == tcp_server.port and not tcp_server.is_running:
        tcp_server.start()

    res = run_tcp_experiment(
        host=host,
        port=port,
        packet_count=packet_count,
        payload_size=payload_size,
        interval_ms=interval_ms,
        timeout_sec=timeout_sec
    )

    if res.get("success"):
        record = storage.save_experiment(
            exp_type="TCP",
            category="REAL_NETWORK",
            config_params=res["config"],
            metrics=res["metrics"],
            status="SUCCESS",
            details={"packets_preview": res["packets"][:20], "notes": res.get("notes")}
        )
        res["saved_record"] = record
        return jsonify(res)
    else:
        return jsonify(res), 500


@app.route("/api/udp/start", methods=["POST"])
def start_udp_experiment():
    """Run real UDP socket experiment."""
    data = request.get_json(silent=True) or {}
    host = data.get("host", DEFAULT_HOST).strip()
    try:
        port = int(data.get("port", DEFAULT_UDP_PORT))
        packet_count = int(data.get("packet_count", 10))
        payload_size = int(data.get("payload_size", 1024))
        interval_ms = float(data.get("interval_ms", 0.0))
        timeout_sec = float(data.get("timeout_sec", 1.0))
        simulated_loss = float(data.get("simulated_loss", 0.0))
    except (ValueError, TypeError) as e:
        return jsonify({"success": False, "error": f"Invalid numerical parameters: {str(e)}"}), 400

    if packet_count < MIN_PACKETS or packet_count > MAX_PACKETS:
        return jsonify({"success": False, "error": f"Packet count must be between {MIN_PACKETS} and {MAX_PACKETS}"}), 400
    if payload_size < MIN_PAYLOAD_SIZE or payload_size > MAX_PAYLOAD_SIZE:
        return jsonify({"success": False, "error": f"Payload size must be between {MIN_PAYLOAD_SIZE} and {MAX_PAYLOAD_SIZE} bytes"}), 400

    # Update demo server loss if targeting local demo server
    if host in ["127.0.0.1", "localhost"] and port == udp_server.port:
        udp_server.set_simulated_loss_rate(simulated_loss)
        if not udp_server.is_running:
            udp_server.start()

    res = run_udp_experiment(
        host=host,
        port=port,
        packet_count=packet_count,
        payload_size=payload_size,
        interval_ms=interval_ms,
        timeout_sec=timeout_sec
    )

    status_str = "SUCCESS" if res["metrics"]["packet_loss_pct"] == 0 else "PARTIAL"
    record = storage.save_experiment(
        exp_type="UDP",
        category="REAL_NETWORK",
        config_params=res["config"],
        metrics=res["metrics"],
        status=status_str,
        details={"packets_preview": res["packets"][:20], "notes": res.get("notes")}
    )
    res["saved_record"] = record
    return jsonify(res)


@app.route("/api/compare/run", methods=["POST"])
def run_comparison_experiment():
    """Run both TCP and UDP with identical parameters for direct performance comparison."""
    data = request.get_json(silent=True) or {}
    try:
        packet_count = int(data.get("packet_count", 20))
        payload_size = int(data.get("payload_size", 1024))
        interval_ms = float(data.get("interval_ms", 0.0))
    except (ValueError, TypeError) as e:
        return jsonify({"success": False, "error": f"Invalid comparison parameters: {str(e)}"}), 400

    # Ensure servers active
    if not tcp_server.is_running:
        tcp_server.start()
    if not udp_server.is_running:
        udp_server.start()

    tcp_res = run_tcp_experiment(
        host=DEFAULT_HOST,
        port=tcp_server.port,
        packet_count=packet_count,
        payload_size=payload_size,
        interval_ms=interval_ms
    )

    udp_res = run_udp_experiment(
        host=DEFAULT_HOST,
        port=udp_server.port,
        packet_count=packet_count,
        payload_size=payload_size,
        interval_ms=interval_ms
    )

    comparison_data = {
        "success": True,
        "config": {
            "packet_count": packet_count,
            "payload_size": payload_size,
            "interval_ms": interval_ms
        },
        "tcp": tcp_res,
        "udp": udp_res,
        "summary": {
            "tcp_throughput": tcp_res["metrics"]["throughput_mbps"] if tcp_res.get("success") else 0,
            "udp_throughput": udp_res["metrics"]["throughput_mbps"] if udp_res.get("success") else 0,
            "tcp_avg_rtt": tcp_res["metrics"]["avg_rtt_ms"] if tcp_res.get("success") else 0,
            "udp_avg_rtt": udp_res["metrics"]["avg_rtt_ms"] if udp_res.get("success") else 0,
            "tcp_loss_pct": tcp_res["metrics"]["packet_loss_pct"] if tcp_res.get("success") else 100,
            "udp_loss_pct": udp_res["metrics"]["packet_loss_pct"] if udp_res.get("success") else 100
        }
    }

    # Save to history
    record = storage.save_experiment(
        exp_type="TCP_VS_UDP_COMPARISON",
        category="REAL_NETWORK",
        config_params=comparison_data["config"],
        metrics={
            "sent_packets": packet_count * 2,
            "received_packets": (
                (tcp_res["metrics"]["received_unique_packets"] if tcp_res.get("success") else 0) +
                (udp_res["metrics"]["received_unique_packets"] if udp_res.get("success") else 0)
            ),
            "tcp_throughput_mbps": comparison_data["summary"]["tcp_throughput"],
            "udp_throughput_mbps": comparison_data["summary"]["udp_throughput"],
            "tcp_avg_rtt_ms": comparison_data["summary"]["tcp_avg_rtt"],
            "udp_avg_rtt_ms": comparison_data["summary"]["udp_avg_rtt"]
        },
        status="SUCCESS",
        details=comparison_data["summary"]
    )
    comparison_data["saved_record"] = record
    return jsonify(comparison_data)


@app.route("/api/leaky-bucket/simulate", methods=["POST"])
def simulate_leaky_bucket():
    """Simulate Leaky Bucket traffic shaper."""
    data = request.get_json(silent=True) or {}
    try:
        capacity = int(data.get("bucket_capacity", 10))
        leak_rate = int(data.get("leak_rate", 3))
        arrivals_raw = data.get("arrival_pattern", [4, 8, 2, 0, 10, 1, 5, 0])
        if isinstance(arrivals_raw, str):
            arrivals = [int(x.strip()) for x in arrivals_raw.split(",") if x.strip()]
        else:
            arrivals = [int(x) for x in arrivals_raw]
    except Exception as e:
        return jsonify({"success": False, "error": f"Invalid Leaky Bucket parameters: {str(e)}"}), 400

    try:
        sim = LeakyBucketSimulator(bucket_capacity=capacity, leak_rate=leak_rate)
        res = sim.simulate(arrival_pattern=arrivals)

        # Save to history
        storage.save_experiment(
            exp_type="LEAKY_BUCKET",
            category="SIMULATION",
            config_params={"bucket_capacity": capacity, "leak_rate": leak_rate, "arrivals": arrivals},
            metrics={
                "sent_packets": res["summary"]["total_incoming"],
                "received_packets": res["summary"]["total_transmitted"],
                "received_unique_packets": res["summary"]["total_transmitted"],
                "packet_loss_pct": res["summary"]["loss_percentage"],
                "delivery_ratio_pct": res["summary"]["delivery_percentage"]
            },
            status="SUCCESS",
            details=res["summary"]
        )

        res["success"] = True
        return jsonify(res)
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400


@app.route("/api/token-bucket/simulate", methods=["POST"])
def simulate_token_bucket():
    """Simulate Token Bucket traffic shaper."""
    data = request.get_json(silent=True) or {}
    try:
        capacity = int(data.get("bucket_capacity", 10))
        token_rate = int(data.get("token_rate", 3))
        queue_capacity = int(data.get("queue_capacity", 10))
        allow_queueing = bool(data.get("allow_queueing", True))
        arrivals_raw = data.get("arrival_pattern", [4, 8, 2, 0, 10, 1, 5, 0])
        if isinstance(arrivals_raw, str):
            arrivals = [int(x.strip()) for x in arrivals_raw.split(",") if x.strip()]
        else:
            arrivals = [int(x) for x in arrivals_raw]
    except Exception as e:
        return jsonify({"success": False, "error": f"Invalid Token Bucket parameters: {str(e)}"}), 400

    try:
        sim = TokenBucketSimulator(
            bucket_capacity=capacity,
            token_rate=token_rate,
            queue_capacity=queue_capacity,
            allow_queueing=allow_queueing
        )
        res = sim.simulate(arrival_pattern=arrivals)

        storage.save_experiment(
            exp_type="TOKEN_BUCKET",
            category="SIMULATION",
            config_params={
                "bucket_capacity": capacity,
                "token_rate": token_rate,
                "queue_capacity": queue_capacity,
                "allow_queueing": allow_queueing,
                "arrivals": arrivals
            },
            metrics={
                "sent_packets": res["summary"]["total_incoming"],
                "received_packets": res["summary"]["total_transmitted"],
                "received_unique_packets": res["summary"]["total_transmitted"],
                "packet_loss_pct": res["summary"]["loss_percentage"],
                "delivery_ratio_pct": res["summary"]["delivery_percentage"]
            },
            status="SUCCESS",
            details=res["summary"]
        )

        res["success"] = True
        return jsonify(res)
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400


@app.route("/api/shaping/compare", methods=["POST"])
def compare_traffic_shaping():
    """Direct side-by-side comparison of Leaky Bucket vs Token Bucket."""
    data = request.get_json(silent=True) or {}
    try:
        capacity = int(data.get("capacity", 10))
        rate = int(data.get("rate", 3))
        arrivals_raw = data.get("arrival_pattern", [4, 8, 2, 0, 10, 1, 5, 0])
        if isinstance(arrivals_raw, str):
            arrivals = [int(x.strip()) for x in arrivals_raw.split(",") if x.strip()]
        else:
            arrivals = [int(x) for x in arrivals_raw]
    except Exception as e:
        return jsonify({"success": False, "error": f"Invalid traffic shaping parameters: {str(e)}"}), 400

    leaky_sim = LeakyBucketSimulator(bucket_capacity=capacity, leak_rate=rate)
    token_sim = TokenBucketSimulator(bucket_capacity=capacity, token_rate=rate, allow_queueing=True)

    leaky_res = leaky_sim.simulate(arrival_pattern=arrivals)
    token_res = token_sim.simulate(arrival_pattern=arrivals)

    return jsonify({
        "success": True,
        "config": {"capacity": capacity, "rate": rate, "arrivals": arrivals},
        "leaky_bucket": leaky_res,
        "token_bucket": token_res
    })


@app.route("/api/congestion/simulate", methods=["POST"])
def simulate_congestion_control():
    """Simulate TCP Congestion Window (Slow Start, Congestion Avoidance, Loss Events)."""
    data = request.get_json(silent=True) or {}
    try:
        mss = int(data.get("mss", 1460))
        initial_cwnd = int(data.get("initial_cwnd", 1))
        initial_ssthresh = int(data.get("initial_ssthresh", 16))
        total_rounds = int(data.get("total_rounds", 25))
        timeout_rounds = data.get("timeout_rounds", [12])
        dup_ack_rounds = data.get("dup_ack_rounds", [20])
    except Exception as e:
        return jsonify({"success": False, "error": f"Invalid Congestion Control parameters: {str(e)}"}), 400

    try:
        sim = TCPCongestionSimulator(
            mss=mss,
            initial_cwnd=initial_cwnd,
            initial_ssthresh=initial_ssthresh
        )
        res = sim.simulate(
            total_rounds=total_rounds,
            timeout_rounds=timeout_rounds,
            dup_ack_rounds=dup_ack_rounds
        )

        storage.save_experiment(
            exp_type="TCP_CONGESTION_CONTROL",
            category="SIMULATION",
            config_params={
                "mss": mss,
                "initial_cwnd": initial_cwnd,
                "initial_ssthresh": initial_ssthresh,
                "total_rounds": total_rounds,
                "timeout_rounds": timeout_rounds,
                "dup_ack_rounds": dup_ack_rounds
            },
            metrics={
                "max_cwnd_mss": res["summary"]["max_cwnd_mss"],
                "final_cwnd_mss": res["summary"]["final_cwnd_mss"],
                "final_ssthresh_mss": res["summary"]["final_ssthresh_mss"],
                "total_events": res["summary"]["total_events"]
            },
            status="SUCCESS",
            details={"events": res["events_log"]}
        )

        res["success"] = True
        return jsonify(res)
    except Exception as ex:
        return jsonify({"success": False, "error": str(ex)}), 400


@app.route("/api/experiments", methods=["GET"])
def get_experiments():
    """Retrieve list of saved experiments."""
    limit = int(request.args.get("limit", 50))
    records = storage.get_all(limit=limit)
    return jsonify({"experiments": records, "count": len(records)})


@app.route("/api/experiments/<exp_id>", methods=["GET"])
def get_experiment_detail(exp_id):
    """Retrieve details for a single experiment run."""
    record = storage.get_by_id(exp_id)
    if not record:
        return jsonify({"error": "Experiment not found"}), 404
    return jsonify(record)


@app.route("/api/experiments/export", methods=["GET"])
def export_experiments_csv():
    """Export experiments as downloadable CSV."""
    csv_data = storage.export_csv()
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=experiments_history.csv"}
    )


@app.route("/api/experiments/clear", methods=["DELETE", "POST"])
def clear_experiments():
    """Clear all experiment history."""
    storage.clear()
    return jsonify({"success": True, "message": "Experiment history cleared"})


@app.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    """Summary metrics for the main dashboard cards."""
    stats = storage.get_summary_stats()
    return jsonify(stats)


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 5000))
    print(f"[STARTING] Starting TCP/UDP Performance Analyzer on http://{host}:{port} ...")
    app.run(host=host, port=port, debug=False)
