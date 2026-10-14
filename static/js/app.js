/**
 * Main Application Logic & Event Controller
 * TCP/UDP Performance Analyzer
 */

// Toast notification helper
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
    <div>${message}</div>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

document.addEventListener('DOMContentLoaded', () => {
  // Navigation handling
  const navItems = document.querySelectorAll('.nav-item');
  const sections = document.querySelectorAll('.view-section');
  const pageTitleElem = document.getElementById('current-page-title');

  function navigateTo(targetId) {
    navItems.forEach(item => {
      if (item.dataset.target === targetId) {
        item.classList.add('active');
        if (pageTitleElem) pageTitleElem.textContent = item.querySelector('.nav-text').textContent;
      } else {
        item.classList.remove('active');
      }
    });

    sections.forEach(sec => {
      if (sec.id === targetId) {
        sec.classList.add('active');
      } else {
        sec.classList.remove('active');
      }
    });

    // Refresh data if landing on dashboard or history
    if (targetId === 'view-dashboard') {
      loadDashboard();
    } else if (targetId === 'view-history') {
      loadHistory();
    }
  }

  navItems.forEach(item => {
    item.addEventListener('click', e => {
      e.preventDefault();
      const target = item.dataset.target;
      navigateTo(target);
    });
  });

  // Server Status Polling & Toggles
  async function refreshServerStatus() {
    try {
      const status = await API.getServerStatus();
      const tcpDot = document.getElementById('tcp-status-dot');
      const tcpText = document.getElementById('tcp-status-text');
      const tcpBtn = document.getElementById('tcp-toggle-btn');

      if (tcpDot && tcpText) {
        if (status.tcp.is_running) {
          tcpDot.className = 'status-dot active';
          tcpText.textContent = `TCP :${status.tcp.port} (Active)`;
          if (tcpBtn) tcpBtn.textContent = 'Stop';
        } else {
          tcpDot.className = 'status-dot inactive';
          tcpText.textContent = `TCP :${status.tcp.port} (Stopped)`;
          if (tcpBtn) tcpBtn.textContent = 'Start';
        }
      }

      const udpDot = document.getElementById('udp-status-dot');
      const udpText = document.getElementById('udp-status-text');
      const udpBtn = document.getElementById('udp-toggle-btn');

      if (udpDot && udpText) {
        if (status.udp.is_running) {
          udpDot.className = 'status-dot active';
          udpText.textContent = `UDP :${status.udp.port} (Active)`;
          if (udpBtn) udpBtn.textContent = 'Stop';
        } else {
          udpDot.className = 'status-dot inactive';
          udpText.textContent = `UDP :${status.udp.port} (Stopped)`;
          if (udpBtn) udpBtn.textContent = 'Start';
        }
      }
    } catch (err) {
      console.warn('Could not poll server status:', err);
    }
  }

  document.getElementById('tcp-toggle-btn')?.addEventListener('click', async () => {
    const btn = document.getElementById('tcp-toggle-btn');
    try {
      if (btn.textContent === 'Stop') {
        await API.stopTcpServer();
        showToast('TCP server stopped', 'info');
      } else {
        await API.startTcpServer(5001);
        showToast('TCP server started on port 5001', 'success');
      }
      refreshServerStatus();
    } catch (e) {
      showToast(e.message, 'error');
    }
  });

  document.getElementById('udp-toggle-btn')?.addEventListener('click', async () => {
    const btn = document.getElementById('udp-toggle-btn');
    try {
      if (btn.textContent === 'Stop') {
        await API.stopUdpServer();
        showToast('UDP server stopped', 'info');
      } else {
        await API.startUdpServer(5002);
        showToast('UDP server started on port 5002', 'success');
      }
      refreshServerStatus();
    } catch (e) {
      showToast(e.message, 'error');
    }
  });

  // Initial and periodic status check
  refreshServerStatus();
  setInterval(refreshServerStatus, 5000);

  // ====================================================================
  // Dashboard Logic
  // ====================================================================
  async function loadDashboard() {
    try {
      const stats = await API.getDashboardStats();
      const experimentsRes = await API.getExperiments(50);
      const experiments = experimentsRes.experiments || [];

      // Update stat cards
      document.getElementById('stat-total-experiments').textContent = stats.total_experiments;
      document.getElementById('stat-total-sent').textContent = stats.total_packets_sent;
      document.getElementById('stat-total-recv').textContent = stats.total_packets_received;
      document.getElementById('stat-avg-latency').textContent = `${stats.overall_avg_latency_ms} ms`;
      document.getElementById('stat-avg-throughput').textContent = `${stats.overall_avg_throughput_mbps} Mbps`;
      document.getElementById('stat-packet-loss').textContent = `${stats.overall_packet_loss_pct}%`;
      document.getElementById('stat-latest-status').textContent = stats.latest_experiment_status;
      document.getElementById('stat-latest-protocol').textContent = stats.latest_experiment_type;

      // Handle empty state vs chart display
      const emptyState = document.getElementById('dashboard-empty-state');
      const chartContainers = document.querySelectorAll('.dashboard-chart-box');

      if (!stats.has_data) {
        if (emptyState) emptyState.style.display = 'block';
        chartContainers.forEach(c => c.style.display = 'none');
      } else {
        if (emptyState) emptyState.style.display = 'none';
        chartContainers.forEach(c => c.style.display = 'block');
        AppCharts.renderDashboardCharts(experiments);
      }
    } catch (err) {
      console.error('Failed to load dashboard stats:', err);
    }
  }

  // Quick Action Start from Dashboard
  document.getElementById('btn-dashboard-start-tcp')?.addEventListener('click', () => {
    navigateTo('view-tcp');
  });
  document.getElementById('btn-dashboard-start-udp')?.addEventListener('click', () => {
    navigateTo('view-udp');
  });

  // ====================================================================
  // TCP Communication Logic
  // ====================================================================
  const tcpForm = document.getElementById('tcp-experiment-form');
  tcpForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-run-tcp');
    const progress = document.getElementById('tcp-progress');
    const progressBar = document.getElementById('tcp-progress-bar');

    btn.disabled = true;
    btn.innerHTML = '⏳ Transmitting packets...';
    if (progress) progress.style.display = 'block';
    if (progressBar) progressBar.style.width = '50%';

    const payload = {
      host: document.getElementById('tcp-host').value.trim(),
      port: parseInt(document.getElementById('tcp-port').value, 10),
      packet_count: parseInt(document.getElementById('tcp-packets').value, 10),
      payload_size: parseInt(document.getElementById('tcp-size').value, 10),
      interval_ms: parseFloat(document.getElementById('tcp-interval').value),
      timeout_sec: parseFloat(document.getElementById('tcp-timeout').value)
    };

    try {
      const res = await API.runTcpExperiment(payload);
      if (progressBar) progressBar.style.width = '100%';

      if (res.success) {
        showToast(`TCP experiment completed: ${res.metrics.received_unique_packets}/${res.metrics.sent_packets} packets delivered`, 'success');
        renderTcpResults(res);
      } else {
        showToast(res.error || 'TCP Experiment failed', 'error');
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = '🚀 Start TCP Experiment';
      setTimeout(() => {
        if (progress) progress.style.display = 'none';
        if (progressBar) progressBar.style.width = '0%';
      }, 500);
      refreshServerStatus();
    }
  });

  function renderTcpResults(data) {
    const m = data.metrics;
    document.getElementById('tcp-res-sent').textContent = m.sent_packets;
    document.getElementById('tcp-res-recv').textContent = m.received_unique_packets;
    document.getElementById('tcp-res-loss').textContent = `${m.packet_loss_pct}%`;
    document.getElementById('tcp-res-delivery').textContent = `${m.delivery_ratio_pct}%`;
    document.getElementById('tcp-res-tp').textContent = `${m.throughput_mbps} Mbps`;
    document.getElementById('tcp-res-avg-rtt').textContent = `${m.avg_rtt_ms} ms`;
    document.getElementById('tcp-res-min-max').textContent = `${m.min_rtt_ms} / ${m.max_rtt_ms} ms`;
    document.getElementById('tcp-res-jitter').textContent = `${m.jitter_ms} ms`;

    // Render table
    const tbody = document.getElementById('tcp-packets-tbody');
    if (tbody) {
      tbody.innerHTML = '';
      data.packets.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>#${p.seq}</strong></td>
          <td>${p.size_bytes} B</td>
          <td>${p.sent_time}s</td>
          <td>${p.ack_time !== null ? p.ack_time + 's' : '-'}</td>
          <td>${p.rtt_ms !== null ? p.rtt_ms + ' ms' : '-'}</td>
          <td><span class="badge ${p.status === 'ACKED' ? 'badge-success' : 'badge-danger'}">${p.status}</span></td>
        `;
        tbody.appendChild(tr);
      });
    }

    // Render Chart
    AppCharts.renderTcpRttChart(data.packets);
    document.getElementById('tcp-results-container').style.display = 'block';
  }

  // ====================================================================
  // UDP Communication Logic
  // ====================================================================
  const udpForm = document.getElementById('udp-experiment-form');
  udpForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-run-udp');
    const progress = document.getElementById('udp-progress');
    const progressBar = document.getElementById('udp-progress-bar');

    btn.disabled = true;
    btn.innerHTML = '⏳ Transmitting datagrams...';
    if (progress) progress.style.display = 'block';
    if (progressBar) progressBar.style.width = '50%';

    const payload = {
      host: document.getElementById('udp-host').value.trim(),
      port: parseInt(document.getElementById('udp-port').value, 10),
      packet_count: parseInt(document.getElementById('udp-packets').value, 10),
      payload_size: parseInt(document.getElementById('udp-size').value, 10),
      interval_ms: parseFloat(document.getElementById('udp-interval').value),
      timeout_sec: parseFloat(document.getElementById('udp-timeout').value),
      simulated_loss: parseFloat(document.getElementById('udp-sim-loss').value)
    };

    try {
      const res = await API.runUdpExperiment(payload);
      if (progressBar) progressBar.style.width = '100%';

      if (res.success) {
        showToast(`UDP experiment completed: ${res.metrics.received_unique_packets}/${res.metrics.sent_packets} ACKs received`, 'success');
        renderUdpResults(res);
      } else {
        showToast(res.error || 'UDP Experiment failed', 'error');
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = '🚀 Start UDP Experiment';
      setTimeout(() => {
        if (progress) progress.style.display = 'none';
        if (progressBar) progressBar.style.width = '0%';
      }, 500);
      refreshServerStatus();
    }
  });

  function renderUdpResults(data) {
    const m = data.metrics;
    document.getElementById('udp-res-sent').textContent = m.sent_packets;
    document.getElementById('udp-res-recv').textContent = m.received_unique_packets;
    document.getElementById('udp-res-loss').textContent = `${m.packet_loss_pct}%`;
    document.getElementById('udp-res-delivery').textContent = `${m.delivery_ratio_pct}%`;
    document.getElementById('udp-res-tp').textContent = `${m.throughput_mbps} Mbps`;
    document.getElementById('udp-res-avg-rtt').textContent = `${m.avg_rtt_ms} ms`;
    document.getElementById('udp-res-min-max').textContent = `${m.min_rtt_ms} / ${m.max_rtt_ms} ms`;
    document.getElementById('udp-res-missing').textContent = m.missing_seqs.length > 0 ? m.missing_seqs.join(', ') : 'None';

    const tbody = document.getElementById('udp-packets-tbody');
    if (tbody) {
      tbody.innerHTML = '';
      data.packets.forEach(p => {
        const tr = document.createElement('tr');
        const isSuccess = p.status === 'ACKED';
        tr.innerHTML = `
          <td><strong>#${p.seq}</strong></td>
          <td>${p.size_bytes} B</td>
          <td>${p.sent_time}s</td>
          <td>${p.ack_time !== null ? p.ack_time + 's' : '-'}</td>
          <td>${p.rtt_ms !== null ? p.rtt_ms + ' ms' : '-'}</td>
          <td><span class="badge ${isSuccess ? 'badge-success' : 'badge-danger'}">${p.status}</span></td>
        `;
        tbody.appendChild(tr);
      });
    }

    AppCharts.renderUdpRttChart(data.packets);
    document.getElementById('udp-results-container').style.display = 'block';
  }

  // ====================================================================
  // Performance Comparison Logic
  // ====================================================================
  const compForm = document.getElementById('comparison-form');
  compForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-run-comparison');
    btn.disabled = true;
    btn.innerHTML = '⏳ Benchmarking TCP & UDP...';

    const payload = {
      packet_count: parseInt(document.getElementById('comp-packets').value, 10),
      payload_size: parseInt(document.getElementById('comp-size').value, 10),
      interval_ms: parseFloat(document.getElementById('comp-interval').value)
    };

    try {
      const res = await API.runComparison(payload);
      if (res.success) {
        showToast('Side-by-side benchmark completed successfully!', 'success');
        renderComparisonResults(res);
      } else {
        showToast(res.error || 'Comparison failed', 'error');
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = '⚖️ Run Direct Side-by-Side Comparison';
      refreshServerStatus();
    }
  });

  function renderComparisonResults(data) {
    const tcpM = data.tcp.metrics;
    const udpM = data.udp.metrics;

    // Fill comparison table
    const tbody = document.getElementById('comparison-table-tbody');
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td><strong style="color: #3b82f6;">TCP (Transmission Control Protocol)</strong></td>
          <td>${tcpM.sent_packets}</td>
          <td>${tcpM.received_unique_packets}</td>
          <td><span class="badge ${tcpM.packet_loss_pct === 0 ? 'badge-success' : 'badge-danger'}">${tcpM.packet_loss_pct}%</span></td>
          <td>${tcpM.avg_rtt_ms} ms</td>
          <td>${tcpM.min_rtt_ms} ms</td>
          <td>${tcpM.max_rtt_ms} ms</td>
          <td><strong>${tcpM.throughput_mbps} Mbps</strong></td>
          <td>${tcpM.elapsed_seconds}s</td>
          <td>${tcpM.delivery_ratio_pct}%</td>
        </tr>
        <tr>
          <td><strong style="color: #06b6d4;">UDP (User Datagram Protocol)</strong></td>
          <td>${udpM.sent_packets}</td>
          <td>${udpM.received_unique_packets}</td>
          <td><span class="badge ${udpM.packet_loss_pct === 0 ? 'badge-success' : 'badge-danger'}">${udpM.packet_loss_pct}%</span></td>
          <td>${udpM.avg_rtt_ms} ms</td>
          <td>${udpM.min_rtt_ms} ms</td>
          <td>${udpM.max_rtt_ms} ms</td>
          <td><strong>${udpM.throughput_mbps} Mbps</strong></td>
          <td>${udpM.elapsed_seconds}s</td>
          <td>${udpM.delivery_ratio_pct}%</td>
        </tr>
      `;
    }

    AppCharts.renderComparisonCharts(tcpM, udpM);
    document.getElementById('comparison-results-container').style.display = 'block';
  }

  // ====================================================================
  // Leaky Bucket Simulation Logic
  // ====================================================================
  const leakyForm = document.getElementById('leaky-bucket-form');
  leakyForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-run-leaky');
    btn.disabled = true;

    const payload = {
      bucket_capacity: parseInt(document.getElementById('leaky-capacity').value, 10),
      leak_rate: parseInt(document.getElementById('leaky-leak-rate').value, 10),
      arrival_pattern: document.getElementById('leaky-arrivals').value.trim()
    };

    try {
      const res = await API.simulateLeakyBucket(payload);
      if (res.success) {
        showToast('Leaky Bucket simulation completed', 'success');
        renderLeakyResults(res);
      } else {
        showToast(res.error || 'Simulation failed', 'error');
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
    }
  });

  document.getElementById('btn-reset-leaky')?.addEventListener('click', () => {
    document.getElementById('leaky-capacity').value = '10';
    document.getElementById('leaky-leak-rate').value = '3';
    document.getElementById('leaky-arrivals').value = '4, 8, 2, 0, 10, 1, 5, 0';
    document.getElementById('leaky-results-container').style.display = 'none';
    AppCharts.destroy('leakyBucketChart');
    showToast('Leaky Bucket settings reset to defaults', 'info');
  });

  function renderLeakyResults(data) {
    const s = data.summary;
    document.getElementById('leaky-res-incoming').textContent = s.total_incoming;
    document.getElementById('leaky-res-transmitted').textContent = s.total_transmitted;
    document.getElementById('leaky-res-dropped').textContent = s.total_dropped;
    document.getElementById('leaky-res-loss').textContent = `${s.loss_percentage}%`;
    document.getElementById('leaky-res-max-queue').textContent = `${s.max_queue_reached} / ${data.capacity}`;
    document.getElementById('leaky-res-util').textContent = `${s.avg_queue_utilization_pct}%`;

    const tbody = document.getElementById('leaky-steps-tbody');
    if (tbody) {
      tbody.innerHTML = '';
      data.steps.forEach(step => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>T=${step.time}</strong></td>
          <td>${step.incoming}</td>
          <td><span style="color:#10b981;">+${step.accepted}</span></td>
          <td><span style="color:${step.dropped > 0 ? '#ef4444' : 'inherit'}; font-weight:${step.dropped > 0 ? '700' : '400'}">${step.dropped}</span></td>
          <td><strong>${step.transmitted}</strong></td>
          <td>${step.queue_after_leak}</td>
          <td>${step.utilization_pct}%</td>
        `;
        tbody.appendChild(tr);
      });
    }

    AppCharts.renderLeakyBucketChart(data.chart_data);
    document.getElementById('leaky-results-container').style.display = 'block';
  }

  // ====================================================================
  // Token Bucket Simulation Logic
  // ====================================================================
  const tokenForm = document.getElementById('token-bucket-form');
  tokenForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-run-token');
    btn.disabled = true;

    const payload = {
      bucket_capacity: parseInt(document.getElementById('token-capacity').value, 10),
      token_rate: parseInt(document.getElementById('token-rate').value, 10),
      queue_capacity: parseInt(document.getElementById('token-queue-cap').value, 10),
      allow_queueing: document.getElementById('token-allow-queue').checked,
      arrival_pattern: document.getElementById('token-arrivals').value.trim()
    };

    try {
      const res = await API.simulateTokenBucket(payload);
      if (res.success) {
        showToast('Token Bucket simulation completed', 'success');
        renderTokenResults(res);
      } else {
        showToast(res.error || 'Simulation failed', 'error');
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
    }
  });

  document.getElementById('btn-reset-token')?.addEventListener('click', () => {
    document.getElementById('token-capacity').value = '10';
    document.getElementById('token-rate').value = '3';
    document.getElementById('token-queue-cap').value = '10';
    document.getElementById('token-allow-queue').checked = true;
    document.getElementById('token-arrivals').value = '4, 8, 2, 0, 10, 1, 5, 0';
    document.getElementById('token-results-container').style.display = 'none';
    AppCharts.destroy('tokenBucketChart');
    showToast('Token Bucket settings reset to defaults', 'info');
  });

  function renderTokenResults(data) {
    const s = data.summary;
    document.getElementById('token-res-incoming').textContent = s.total_incoming;
    document.getElementById('token-res-transmitted').textContent = s.total_transmitted;
    document.getElementById('token-res-dropped').textContent = s.total_dropped;
    document.getElementById('token-res-loss').textContent = `${s.loss_percentage}%`;
    document.getElementById('token-res-bursts').textContent = s.burst_events;
    document.getElementById('token-res-peak-burst').textContent = `${s.max_burst_size} pkts`;

    const tbody = document.getElementById('token-steps-tbody');
    if (tbody) {
      tbody.innerHTML = '';
      data.steps.forEach(step => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><strong>T=${step.time}</strong></td>
          <td>${step.incoming}</td>
          <td>${step.tokens_available}</td>
          <td>
            <strong>${step.transmitted}</strong>
            ${step.is_burst ? '<span class="badge badge-warning" style="margin-left:4px;">BURST</span>' : ''}
          </td>
          <td>${step.tokens_consumed}</td>
          <td>${step.tokens_remaining}</td>
          <td>${step.queue_size}</td>
          <td><span style="color:${step.dropped > 0 ? '#ef4444' : 'inherit'}">${step.dropped}</span></td>
        `;
        tbody.appendChild(tr);
      });
    }

    AppCharts.renderTokenBucketChart(data.chart_data);
    document.getElementById('token-results-container').style.display = 'block';
  }

  // Quick Compare Shaping algorithms directly
  document.getElementById('btn-compare-shaping')?.addEventListener('click', async () => {
    const cap = parseInt(document.getElementById('token-capacity').value, 10);
    const rate = parseInt(document.getElementById('token-rate').value, 10);
    const arr = document.getElementById('token-arrivals').value.trim();

    try {
      const res = await API.compareTrafficShaping({ capacity: cap, rate: rate, arrival_pattern: arr });
      if (res.success) {
        showToast('Comparing Leaky vs Token Bucket output!', 'info');
        // Switch to Leaky view to show comparison or display modal
        showModal(
          'Traffic Shaping Comparison: Leaky Bucket vs Token Bucket',
          `
          <p><strong>Config:</strong> Capacity = ${cap}, Rate = ${rate}/step</p>
          <div style="margin: 14px 0;">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Algorithm</th>
                  <th>Total Incoming</th>
                  <th>Transmitted</th>
                  <th>Dropped</th>
                  <th>Loss %</th>
                  <th>Burst Allowed?</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>Leaky Bucket</strong></td>
                  <td>${res.leaky_bucket.summary.total_incoming}</td>
                  <td>${res.leaky_bucket.summary.total_transmitted}</td>
                  <td>${res.leaky_bucket.summary.total_dropped}</td>
                  <td>${res.leaky_bucket.summary.loss_percentage}%</td>
                  <td><span class="badge badge-info">No (Fixed Rate)</span></td>
                </tr>
                <tr>
                  <td><strong>Token Bucket</strong></td>
                  <td>${res.token_bucket.summary.total_incoming}</td>
                  <td>${res.token_bucket.summary.total_transmitted}</td>
                  <td>${res.token_bucket.summary.total_dropped}</td>
                  <td>${res.token_bucket.summary.loss_percentage}%</td>
                  <td><span class="badge badge-success">Yes (${res.token_bucket.summary.burst_events} bursts)</span></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="concept-box">
            <h4>Key Educational Takeaway:</h4>
            <strong>Leaky Bucket</strong> strictly shapes output to a constant rate (${rate} pkts/step), smoothing out all burstiness at the cost of higher queuing delay or overflow drops.<br/>
            <strong>Token Bucket</strong> permits momentary bursts (up to bucket capacity ${cap}) if idle periods allowed tokens to accumulate, better utilizing instantaneous bandwidth for bursty applications (like web browsing and video streaming).
          </div>
          `
        );
      }
    } catch (e) {
      showToast(e.message, 'error');
    }
  });

  // ====================================================================
  // TCP Congestion Window Simulation Logic
  // ====================================================================
  const congestionForm = document.getElementById('congestion-form');
  congestionForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('btn-run-congestion');
    btn.disabled = true;

    const timeoutStr = document.getElementById('cong-timeout-rounds').value.trim();
    const timeoutRounds = timeoutStr ? timeoutStr.split(',').map(x => parseInt(x.trim(), 10)).filter(x => !isNaN(x)) : [];

    const dupStr = document.getElementById('cong-dup-ack-rounds').value.trim();
    const dupRounds = dupStr ? dupStr.split(',').map(x => parseInt(x.trim(), 10)).filter(x => !isNaN(x)) : [];

    const payload = {
      mss: parseInt(document.getElementById('cong-mss').value, 10),
      initial_cwnd: parseInt(document.getElementById('cong-init-cwnd').value, 10),
      initial_ssthresh: parseInt(document.getElementById('cong-init-ssthresh').value, 10),
      total_rounds: parseInt(document.getElementById('cong-rounds').value, 10),
      timeout_rounds: timeoutRounds,
      dup_ack_rounds: dupRounds
    };

    try {
      const res = await API.simulateCongestion(payload);
      if (res.success) {
        showToast('TCP Congestion Window simulation completed', 'success');
        renderCongestionResults(res);
      } else {
        showToast(res.error || 'Simulation failed', 'error');
      }
    } catch (err) {
      showToast(err.message, 'error');
    } finally {
      btn.disabled = false;
    }
  });

  // Presets
  document.getElementById('btn-preset-standard')?.addEventListener('click', () => {
    document.getElementById('cong-init-ssthresh').value = '16';
    document.getElementById('cong-rounds').value = '25';
    document.getElementById('cong-timeout-rounds').value = '12';
    document.getElementById('cong-dup-ack-rounds').value = '20';
    congestionForm.dispatchEvent(new Event('submit'));
  });

  document.getElementById('btn-preset-heavy-loss')?.addEventListener('click', () => {
    document.getElementById('cong-init-ssthresh').value = '12';
    document.getElementById('cong-rounds').value = '30';
    document.getElementById('cong-timeout-rounds').value = '8, 18';
    document.getElementById('cong-dup-ack-rounds').value = '24';
    congestionForm.dispatchEvent(new Event('submit'));
  });

  function renderCongestionResults(data) {
    const s = data.summary;
    document.getElementById('cong-res-max-cwnd').textContent = `${s.max_cwnd_mss} MSS`;
    document.getElementById('cong-res-final-cwnd').textContent = `${s.final_cwnd_mss} MSS`;
    document.getElementById('cong-res-final-thresh').textContent = `${s.final_ssthresh_mss} MSS`;
    document.getElementById('cong-res-phase').textContent = s.final_phase;
    document.getElementById('cong-res-events-count').textContent = s.total_events;

    // Timeline table
    const tbody = document.getElementById('cong-rounds-tbody');
    if (tbody) {
      tbody.innerHTML = '';
      data.rounds_data.forEach(r => {
        const tr = document.createElement('tr');
        let phaseBadge = '<span class="badge badge-info">Slow Start</span>';
        if (r.phase === 'Congestion Avoidance') {
          phaseBadge = '<span class="badge badge-success">Avoidance</span>';
        }

        if (r.event_type === 'TIMEOUT') {
          phaseBadge = '<span class="badge badge-danger">TIMEOUT</span>';
        } else if (r.event_type === 'FAST_RECOVERY') {
          phaseBadge = '<span class="badge badge-warning">3 DUP ACKS</span>';
        }

        tr.innerHTML = `
          <td><strong>Round ${r.round}</strong></td>
          <td>${r.rtt_ms} ms</td>
          <td><strong>${r.cwnd_mss} MSS</strong> (${r.cwnd_bytes.toLocaleString()} B)</td>
          <td>${r.ssthresh_mss} MSS</td>
          <td>${phaseBadge}</td>
          <td style="font-size:12px; color:var(--text-muted);">${r.description}</td>
        `;
        tbody.appendChild(tr);
      });
    }

    AppCharts.renderCongestionChart(data.chart_data);
    document.getElementById('congestion-results-container').style.display = 'block';
  }

  // ====================================================================
  // Experiment History Logic
  // ====================================================================
  async function loadHistory() {
    try {
      const res = await API.getExperiments(50);
      const records = res.experiments || [];
      const tbody = document.getElementById('history-table-tbody');
      const emptyState = document.getElementById('history-empty-state');
      const tableWrapper = document.getElementById('history-table-container');

      if (!records || records.length === 0) {
        if (emptyState) emptyState.style.display = 'block';
        if (tableWrapper) tableWrapper.style.display = 'none';
        return;
      }

      if (emptyState) emptyState.style.display = 'none';
      if (tableWrapper) tableWrapper.style.display = 'block';

      if (tbody) {
        tbody.innerHTML = '';
        records.forEach(r => {
          const m = r.metrics || {};
          const tr = document.createElement('tr');
          const isReal = r.category === 'REAL_NETWORK';

          let statusBadge = `<span class="badge badge-success">${r.status}</span>`;
          if (r.status === 'PARTIAL') statusBadge = `<span class="badge badge-warning">${r.status}</span>`;
          if (r.status === 'FAILED') statusBadge = `<span class="badge badge-danger">${r.status}</span>`;

          const sent = m.sent_packets ?? m.total_packets ?? '-';
          const recv = m.received_unique_packets ?? m.received_packets ?? m.total_transmitted ?? '-';
          const loss = m.packet_loss_pct ?? m.loss_percentage ?? '-';
          const latency = m.avg_rtt_ms !== undefined ? `${m.avg_rtt_ms} ms` : '-';
          const throughput = m.throughput_mbps !== undefined ? `${m.throughput_mbps} Mbps` : '-';

          tr.innerHTML = `
            <td><code>${r.id}</code></td>
            <td>${r.readable_time || r.timestamp}</td>
            <td><span class="badge ${isReal ? 'badge-info' : 'badge-warning'}">${r.type}</span></td>
            <td>${sent}</td>
            <td>${recv}</td>
            <td>${loss !== '-' ? loss + '%' : '-'}</td>
            <td>${latency}</td>
            <td>${throughput}</td>
            <td>${statusBadge}</td>
            <td>
              <button class="btn btn-secondary btn-sm" onclick="viewHistoryDetail('${r.id}')" style="padding:4px 8px; font-size:11px;">View</button>
            </td>
          `;
          tbody.appendChild(tr);
        });
      }
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  }

  // Export CSV
  document.getElementById('btn-export-csv')?.addEventListener('click', () => {
    window.location.href = API.getExportUrl();
    showToast('Exporting experiment history to CSV...', 'info');
  });

  // Clear History
  document.getElementById('btn-clear-history')?.addEventListener('click', async () => {
    if (confirm('Are you sure you want to clear all experiment history records? This cannot be undone.')) {
      try {
        await API.clearHistory();
        showToast('All experiment history cleared', 'success');
        loadHistory();
        loadDashboard();
      } catch (err) {
        showToast(err.message, 'error');
      }
    }
  });

  // Global detail viewer
  window.viewHistoryDetail = async (id) => {
    try {
      const record = await API.getExperimentDetail(id);
      showModal(
        `Experiment Details: ${record.id}`,
        `
        <div style="display:flex; gap:12px; margin-bottom:12px;">
          <span class="badge badge-info">${record.type}</span>
          <span class="badge ${record.category === 'REAL_NETWORK' ? 'badge-success' : 'badge-warning'}">${record.category}</span>
          <span style="color:var(--text-muted); font-size:12px;">${record.readable_time}</span>
        </div>
        <h4 style="margin-bottom:6px; color:#ffffff;">Configuration:</h4>
        <pre class="formula-card">${JSON.stringify(record.config, null, 2)}</pre>
        <h4 style="margin-bottom:6px; color:#ffffff;">Metrics:</h4>
        <pre class="formula-card">${JSON.stringify(record.metrics, null, 2)}</pre>
        `
      );
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  // Modal helper
  function showModal(title, contentHtml) {
    const backdrop = document.getElementById('modal-backdrop');
    const titleEl = document.getElementById('modal-title');
    const bodyEl = document.getElementById('modal-body');

    if (titleEl) titleEl.textContent = title;
    if (bodyEl) bodyEl.innerHTML = contentHtml;
    if (backdrop) backdrop.classList.add('open');
  }

  document.getElementById('btn-close-modal')?.addEventListener('click', () => {
    document.getElementById('modal-backdrop')?.classList.remove('open');
  });

  document.getElementById('modal-backdrop')?.addEventListener('click', (e) => {
    if (e.target.id === 'modal-backdrop') {
      document.getElementById('modal-backdrop')?.classList.remove('open');
    }
  });

  // Initial dashboard load
  loadDashboard();
});
