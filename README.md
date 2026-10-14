# TCP/UDP Client–Server Communication and Performance Analyzer

A full-stack, modular, and beginner-friendly Computer Networks project designed for B.Tech Computer Science and Data Science curriculum demonstrations. This application pairs real operating-system socket communication (TCP and UDP) with mathematical performance calculations, traffic-shaping algorithm simulations (Leaky Bucket & Token Bucket), and TCP congestion-control modeling (Slow Start, Congestion Avoidance, Fast Retransmit).

---

## 📑 Table of Contents
1. [Project Overview](#1-project-overview)
2. [Problem Statement & Objectives](#2-problem-statement--objectives)
3. [Software Requirements](#3-software-requirements)
4. [Architecture & System Design](#4-architecture--system-design)
5. [Folder Structure](#5-folder-structure)
6. [Installation & Quick Start (Windows & Linux)](#6-installation--quick-start)
7. [How to Conduct Experiments](#7-how-to-conduct-experiments)
8. [Algorithms Explained](#8-algorithms-explained)
9. [Performance Formulas](#9-performance-formulas)
10. [REST API Documentation](#10-rest-api-documentation)
11. [Running Automated Tests](#11-running-automated-tests)
12. [Expected Observations](#12-expected-observations)
13. [College Viva Voce Q&A Cheat Sheet](#13-college-viva-voce-qa-cheat-sheet)
14. [Limitations & Scope](#14-limitations--scope)

---

## 1. Project Overview

In computer networking courses, students often study transport layer protocols (TCP and UDP) and traffic policing algorithms purely from textbooks. This project bridges theory and practice by providing:
- **Actual Local Sockets:** Real TCP stream sockets and UDP datagram sockets exchanging frames on localhost with sequence tracking and timestamps.
- **Traffic Shaping Simulators:** Discrete-time implementations of the **Leaky Bucket** and **Token Bucket** algorithms.
- **TCP Congestion Control Simulator:** Visual educational simulation of the **TCP Reno** congestion window (`cwnd`) responding to slow start, additive increase, timeouts, and 3-duplicate ACKs.
- **Professional Dashboard:** Dark navy and blue user interface with real-time Chart.js graphs, experiment persistence, and CSV export.

---

## 2. Problem Statement & Objectives

### Problem Statement
Standard socket programming exercises in universities are typically command-line scripts that send a single string (`"Hello World"`) without performance instrumentation, message framing, or traffic policing context. Students miss understanding:
- How streaming byte boundaries differ from datagram boundaries.
- Why TCP latency is influenced by round-trip acknowledgements.
- How queue buffers and token buckets shape bursty network traffic.
- How TCP dynamically senses network congestion via packet loss.

### Objectives
1. Implement real TCP client-server communication using **length-prefixed message framing**.
2. Implement real UDP datagram client-server communication with per-packet socket timeouts and simulated loss handling.
3. Calculate and display accurate network metrics: **Throughput (Mbps)**, **Packet Loss (%)**, **Delivery Ratio (%)**, and **Average RTT Latency (ms)**.
4. Implement deterministic simulations of **Leaky Bucket** and **Token Bucket** algorithms.
5. Provide a visual educational simulation of the **TCP Congestion Window (`cwnd`)** across RTT rounds.
6. Record experiment runs to persistent storage with CSV export capabilities.

---

## 3. Software Requirements

- **Operating System:** Windows 10/11, macOS, or Linux
- **Python:** Python 3.8+ (tested on Python 3.10 – 3.14)
- **Web Browser:** Google Chrome, Microsoft Edge, Mozilla Firefox, or Safari
- **Python Dependencies:** `Flask` (>= 2.3.0)
- **Frontend Dependencies:** Chart.js (loaded via CDN, vanilla CSS3, vanilla ES6 JavaScript)

---

## 4. Architecture & System Design

```
+--------------------------------------------------------------------------+
|                     Modern Dark Navy Web Dashboard                       |
|           (HTML5 / Vanilla CSS3 / Vanilla JS / Chart.js v4)              |
+------------------------------------+-------------------------------------+
                                     | REST API (JSON)
+------------------------------------v-------------------------------------+
|                      Flask Application (`app.py`)                        |
+------------------+------------------+------------------+-----------------+
                   |                  |                  |
+------------------v---+    +---------v--------+   +-----v---------------+
| Real Networking Sockets | | Traffic Algorithms | | Storage & History   |
| - TCP Server/Client  |    | - Leaky Bucket   |   | - JSON persistence  |
|   (Length Framing)   |    | - Token Bucket   |   | - CSV Exporter      |
| - UDP Server/Client  |    | - TCP Congestion |   |                     |
|   (Datagram Timeout) |    |   Simulator      |   |                     |
+----------------------+    +------------------+   +---------------------+
                   |
+------------------v-----------------------------------------------------+
|                   Performance Calculation Engine                       |
|   Throughput (Mbps) | Packet Loss (%) | Delivery Ratio (%) | RTT (ms)  |
+------------------------------------------------------------------------+
```

---

## 5. Folder Structure

```
TCP-UDP-Performance-Analyzer/
├── app.py                     # Main Flask web application & REST endpoints
├── config.py                  # Default ports, packet boundaries, storage paths
├── requirements.txt           # Minimal Python dependencies
├── test_all.py                # Master test runner
├── README.md                  # Comprehensive project and viva documentation
│
├── networking/                # Real Python socket implementations
│   ├── __init__.py
│   ├── tcp_server.py          # Multithreaded TCP server with length-prefixed framing
│   ├── tcp_client.py          # TCP client measuring sequence RTT & throughput
│   ├── udp_server.py          # UDP datagram server with simulated drop rate
│   └── udp_client.py          # UDP datagram client with socket timeouts
│
├── algorithms/                # Network algorithm implementations
│   ├── __init__.py
│   ├── leaky_bucket.py        # Discrete-time Leaky Bucket traffic shaper
│   ├── token_bucket.py        # Token Bucket burst-tolerant traffic shaper
│   └── congestion_window.py   # TCP Reno cwnd & ssthresh simulation
│
├── analyzer/                  # Performance formulas & metrics
│   ├── __init__.py
│   └── performance.py         # Safe throughput, loss, latency, jitter calculations
│
├── storage/                   # Experiment persistence
│   ├── __init__.py
│   └── experiment_history.py  # Thread-safe JSON storage & CSV export
│
├── templates/
│   └── index.html             # Single-page application dashboard layout
│
├── static/
│   ├── css/
│   │   └── style.css          # Dark navy & blue responsive design system
│   └── js/
│       ├── api.js             # Async REST API client
│       ├── charts.js          # Chart.js initialization and updates
│       └── app.js             # View controller, forms, progress & notifications
│
├── tests/                     # Unit and integration test suite
│   ├── __init__.py
│   ├── test_performance.py    # Metric formula verification
│   ├── test_leaky_bucket.py   # Leaky Bucket queue overflow tests
│   ├── test_token_bucket.py   # Token Bucket burst tests
│   ├── test_congestion.py     # Congestion window phase transition tests
│   ├── test_tcp.py            # Local TCP socket integration tests
│   └── test_udp.py            # Local UDP datagram socket integration tests
│
└── results/
    └── experiments.json       # Automatically generated history storage
```

---

## 6. Installation & Quick Start

### Step 1: Clone or Navigate to the Workspace
Open Command Prompt or PowerShell in the project directory:
```cmd
cd "c:\Users\DELL\Documents\TCP UDP project"
```

### Step 2: Create and Activate a Python Virtual Environment
**On Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```cmd
pip install -r requirements.txt
```

### Step 4: Run the Application
```cmd
python app.py
```
Output:
```
🚀 Starting TCP/UDP Performance Analyzer on http://127.0.0.1:5000 ...
```

### Step 5: Open the Web Dashboard
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```
The TCP server on port `5001` and UDP server on port `5002` start automatically in background daemon threads.

---

## 7. How to Conduct Experiments

### Experiment 1: Measuring TCP Reliability and Latency
1. In the sidebar, select **TCP Communication**.
2. Set **Number of Packets** (e.g., `20`), **Payload Size** (e.g., `1024` bytes), and **Interval Delay** (e.g., `5` ms).
3. Click **🚀 Start TCP Experiment**.
4. Observe:
   - All packets are sequentially transmitted and acknowledged.
   - Delivery ratio is 100% and packet loss is 0.0%.
   - Chart.js renders the RTT latency curve per sequence number.

### Experiment 2: Measuring UDP Datagram Transmission & Loss
1. In the sidebar, select **UDP Communication**.
2. Keep the default port `5002`. Set **Educational Simulated Loss** to `25% Packet Drop Rate`.
3. Click **🚀 Start UDP Experiment**.
4. Observe:
   - Lost packets trigger socket timeouts and are captured as `TIMEOUT_LOST`.
   - The missing sequence numbers are enumerated in the summary card (e.g., `Missing Sequences: 3, 7, 14`).
   - The RTT chart shows discontinuities for dropped datagrams.

### Experiment 3: Direct Performance Comparison
1. In the sidebar, select **Performance Comparison**.
2. Specify matching parameters (e.g., 20 packets, 1024 bytes).
3. Click **⚖️ Run Direct Side-by-Side Comparison**.
4. Observe the side-by-side comparison table and multi-metric bar chart comparing throughput, latency, and delivery ratio under identical local conditions.

### Experiment 4: Leaky Bucket Traffic Smoothing
1. In the sidebar, select **Leaky Bucket**.
2. Input Capacity = `10`, Leak Rate = `3`, Arrivals = `4, 8, 2, 0, 10, 1, 5, 0`.
3. Click **🚀 Run Simulation**.
4. Observe:
   - Bursts exceeding capacity are dropped immediately.
   - The transmitted stream is flat and smooth, strictly bounded by the leak rate.

### Experiment 5: Token Bucket Burst Handling
1. In the sidebar, select **Token Bucket**.
2. Input Capacity = `10`, Token Rate = `3`, Arrivals = `4, 8, 2, 0, 10, 1, 5, 0`.
3. Click **🚀 Run Simulation**.
4. Observe:
   - Initial accumulated tokens allow the incoming burst to transmit immediately (`BURST` badge).
   - Click **⚖️ Compare Directly with Leaky Bucket** to inspect differences side-by-side.

### Experiment 6: TCP Congestion Window Dynamics
1. In the sidebar, select **TCP Congestion Window**.
2. Click **Standard Reno Scenario** (Initial threshold: 16 MSS, Timeout at Round 12, 3 Dup ACKs at Round 20).
3. Click **🚀 Run Simulation**.
4. Observe:
   - **Rounds 1–5:** Slow Start exponential growth ($1 \to 2 \to 4 \to 8 \to 16$).
   - **Rounds 6–11:** Congestion Avoidance additive increase ($16 \to 17 \to 18 \dots$).
   - **Round 12:** Timeout! `ssthresh` halves to 11, `cwnd` crashes to 1.
   - **Round 20:** Fast Recovery (3 Dup ACKs)! `cwnd` drops to `ssthresh` without crashing to 1.

---

## 8. Algorithms Explained

### Leaky Bucket Algorithm
- **Concept:** Models a bucket with a fixed orifice at the bottom.
- **Behavior:** No matter how irregularly packets enter the bucket, they exit at a fixed, uniform rate (`leak_rate`). If packets arrive faster than the buffer can accommodate (`capacity`), the excess spills over and is discarded.
- **Best for:** Traffic policing where a strict, non-bursty traffic contract is required (e.g., ATM networks, telecommunications voice channels).

### Token Bucket Algorithm
- **Concept:** Tokens are continuously added to a bucket of maximum capacity at rate $r$.
- **Behavior:** Each outgoing packet requires 1 (or $k$) tokens to transmit. If tokens are available, packets are dispatched immediately. If tokens are exhausted, packets wait in a queue or drop.
- **Key Advantage over Leaky Bucket:** Allows momentary bursts of traffic up to the bucket capacity while maintaining a guaranteed average transmission rate. Ideal for web browsing and HTTP streaming.

### TCP Congestion Control (Reno Model)
TCP uses implicit feedback (loss/timeouts) to sense link capacity without router assistance:
1. **Slow Start ($cwnd < ssthresh$):** For each ACK received, $cwnd = cwnd + 1 \text{ MSS}$, resulting in an exponential doubling of $cwnd$ every RTT.
2. **Congestion Avoidance ($cwnd \ge ssthresh$):** Increases linearly: $cwnd = cwnd + 1 \text{ MSS}$ per RTT.
3. **Timeout (Severe Loss):** $ssthresh = \max(2, cwnd / 2)$, $cwnd = 1 \text{ MSS}$, reset to Slow Start.
4. **Fast Retransmit & Recovery (3 Duplicate ACKs):** $ssthresh = \max(2, cwnd / 2)$, $cwnd = ssthresh$, resumes Congestion Avoidance immediately.

---

## 9. Performance Formulas

### 1. Throughput (Mbps)
Calculates effective application payload rate (Goodput):
$$\text{Throughput (Mbps)} = \frac{\text{Successfully Received Payload Bytes} \times 8}{\text{Elapsed Seconds} \times 1,000,000}$$

### 2. Packet Loss Percentage (%)
$$\text{Packet Loss (\%)} = \left(\frac{\text{Sent Packets} - \text{Received Unique Packets}}{\text{Sent Packets}}\right) \times 100$$

### 3. Delivery Ratio (%)
$$\text{Delivery Ratio (\%)} = \left(\frac{\text{Received Unique Packets}}{\text{Sent Packets}}\right) \times 100$$

### 4. Average Round-Trip Time (ms)
$$\text{Average RTT (ms)} = \frac{\sum_{i=1}^{N} \text{Measured RTT}_i}{N}$$

---

## 10. REST API Documentation

| Endpoint | Method | Description | Sample Request / Response |
| :--- | :---: | :--- | :--- |
| `/api/health` | `GET` | Health check and runtime information | `{"status": "healthy", "version": "1.0.0"}` |
| `/api/servers/status` | `GET` | Real-time status of TCP & UDP demonstration servers | Returns listening ports and active flags |
| `/api/servers/tcp/start` | `POST` | Start TCP demonstration server | `{"port": 5001}` |
| `/api/servers/tcp/stop` | `POST` | Stop TCP demonstration server | `{"status": "STOPPED"}` |
| `/api/servers/udp/start` | `POST` | Start UDP demonstration server | `{"port": 5002, "simulate_loss_rate": 0.1}` |
| `/api/servers/udp/stop` | `POST` | Stop UDP demonstration server | `{"status": "STOPPED"}` |
| `/api/tcp/start` | `POST` | Execute real TCP socket experiment | Body: `host, port, packet_count, payload_size, interval_ms, timeout_sec` |
| `/api/udp/start` | `POST` | Execute real UDP socket experiment | Body: `host, port, packet_count, payload_size, interval_ms, timeout_sec, simulated_loss` |
| `/api/compare/run` | `POST` | Execute matching TCP and UDP benchmarks | Body: `packet_count, payload_size, interval_ms` |
| `/api/leaky-bucket/simulate` | `POST` | Run Leaky Bucket traffic simulation | Body: `bucket_capacity, leak_rate, arrival_pattern` |
| `/api/token-bucket/simulate` | `POST` | Run Token Bucket traffic simulation | Body: `bucket_capacity, token_rate, queue_capacity, allow_queueing, arrival_pattern` |
| `/api/shaping/compare` | `POST` | Direct comparative simulation of Leaky vs Token | Body: `capacity, rate, arrival_pattern` |
| `/api/congestion/simulate` | `POST` | Run educational TCP Congestion simulation | Body: `mss, initial_cwnd, initial_ssthresh, total_rounds, timeout_rounds, dup_ack_rounds` |
| `/api/experiments` | `GET` | Retrieve saved experiment runs | `?limit=50` |
| `/api/experiments/<id>` | `GET` | Retrieve detailed metrics and trace for single run | Returns JSON record |
| `/api/experiments/export` | `GET` | Download experiment history as CSV file | Returns `experiments_history.csv` |
| `/api/experiments/clear` | `DELETE` | Clear all history records | `{"success": true}` |
| `/api/dashboard/stats` | `GET` | Summary statistics for dashboard cards | Aggregated counts, loss %, avg throughput |

---

## 11. Running Automated Tests

Run the master test suite using Python's standard `unittest` framework:

```cmd
python test_all.py
```

Or using module discovery:
```cmd
python -m unittest discover tests -v
```

### Verified Test Cases
1. `test_performance.py`: Verified zero-division handling, packet loss calculations, throughput formula, and jitter.
2. `test_leaky_bucket.py`: Verified queue capacity overflow, leak rate smoothing, and parameter boundaries.
3. `test_token_bucket.py`: Verified burst transmissions up to capacity and queueing vs dropping behaviors.
4. `test_congestion.py`: Verified Slow Start exponential growth, Congestion Avoidance additive increase, timeout crash to 1 MSS, and Fast Recovery half-cut.
5. `test_tcp.py`: Verified socket binding, length-prefixed framing, ACK round-trip measurement, and connection refused handling.
6. `test_udp.py`: Verified datagram transmission, ACK reception, and socket timeout handling for missing packets.

---

## 12. Expected Observations

1. **TCP Delivery Guarantee:** Under normal operating conditions, TCP packet loss is 0.0% and delivery ratio is 100%, owing to the reliable byte-stream and connection handshake.
2. **TCP Framing:** Because TCP is a continuous byte stream, receiving messages without framing can cause concatenated or fragmented payloads. The project's 4-byte big-endian length prefix ensures 100% boundary integrity.
3. **UDP Best-Effort:** When simulated loss is active, UDP loses packets without automatic retransmission. The client timeout records the missing sequence numbers cleanly.
4. **Leaky Bucket vs Token Bucket:** When subjected to an identical burst (e.g., 10 packets arriving in slot 1 with rate 3), Leaky Bucket spreads transmission across multiple slots (3, 3, 3, 1), whereas Token Bucket transmits up to its available token balance in slot 1 as an immediate burst.
5. **Congestion Window:** Demonstrates why TCP initially starts slowly before quickly ramping up throughput, and why Fast Recovery (3 Dup ACKs) is substantially more efficient than waiting for a Retransmission Timeout.

---

## 13. College Viva Voce Q&A Cheat Sheet

**Q1: What is the difference between TCP and UDP at the transport layer?**  
*Answer:* TCP is connection-oriented, reliable, and byte-stream based. It establishes a 3-way handshake, guarantees in-order delivery, and provides flow/congestion control. UDP is connectionless, unreliable, and datagram-based. It offers minimal overhead (8-byte header vs 20–60 bytes) and zero delivery guarantees.

**Q2: Why does TCP require message framing?**  
*Answer:* TCP treats all data as an unstructured stream of bytes. Calling `send()` twice does not guarantee two `recv()` calls; the data may arrive concatenated or fragmented. Length-prefixed framing (sending a 4-byte integer length before each payload) guarantees that the receiver knows exactly how many bytes to read for each complete message.

**Q3: How does Token Bucket allow traffic bursts while Leaky Bucket does not?**  
*Answer:* Leaky Bucket operates like a bucket with a fixed hole; packets leave at a constant rate regardless of how many have accumulated. Token Bucket accumulates tokens during idle periods; when a burst arrives, packets can consume all accumulated tokens and transmit immediately up to bucket capacity.

**Q4: What causes a TCP sender to transition from Slow Start to Congestion Avoidance?**  
*Answer:* When the congestion window (`cwnd`) reaches or exceeds the slow-start threshold (`ssthresh`), TCP transitions from exponential growth to linear Additive Increase (+1 MSS per RTT) to avoid overwhelming intermediate routers.

**Q5: What is the difference between a Timeout and 3 Duplicate ACKs?**  
*Answer:* A Timeout means no ACKs are returning, suggesting severe network congestion; TCP resets `cwnd` to 1 MSS. Three Duplicate ACKs indicate out-of-order delivery caused by a single dropped packet while subsequent packets continue to arrive; TCP triggers Fast Retransmit and Fast Recovery, cutting `cwnd` in half without dropping to 1 MSS.

---

## 14. Limitations & Scope

- **Localhost Loopback:** Experiments run over the loopback interface (`127.0.0.1`), where physical network propagation delay and physical packet loss are negligible (near 0 ms latency). Simulated loss is provided to demonstrate UDP loss behavior.
- **Educational Congestion Simulator:** The congestion window simulator models TCP Reno mathematically rather than extracting kernel TCP variables (`tcp_info`), ensuring deterministic, platform-independent demonstration on any Windows or Linux environment.
- **Application-Level Goodput:** Throughput measurements calculate application-level payload bytes delivered per second, distinguishing application goodput from transport/link layer packet headers.

---

## 15. Authors & Acknowledgements
- **Curriculum:** Computer Networks Laboratory (B.Tech CSE / Data Science)
- **Built with:** Python, Flask, Sockets, Vanilla CSS3, Chart.js
