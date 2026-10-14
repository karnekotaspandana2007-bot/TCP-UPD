/**
 * Chart.js Visualizations Manager for TCP/UDP Performance Analyzer
 */
const AppCharts = {
  instances: {},

  // Global theme settings for dark navy background
  getChartDefaults() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 12 }
          }
        },
        tooltip: {
          backgroundColor: '#0f172a',
          titleColor: '#ffffff',
          bodyColor: '#cbd5e1',
          borderColor: '#1e293b',
          borderWidth: 1,
          padding: 10,
          cornerRadius: 6
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(30, 41, 59, 0.4)' },
          ticks: { color: '#64748b', font: { family: 'Inter', size: 11 } }
        },
        y: {
          grid: { color: 'rgba(30, 41, 59, 0.4)' },
          ticks: { color: '#64748b', font: { family: 'Inter', size: 11 } }
        }
      }
    };
  },

  destroy(canvasId) {
    if (this.instances[canvasId]) {
      this.instances[canvasId].destroy();
      delete this.instances[canvasId];
    }
  },

  // 1. Dashboard Throughput & Latency Charts
  renderDashboardCharts(historyRecords) {
    if (!window.Chart) return;

    // Filter real network records
    const realRecs = historyRecords.filter(r => r.category === 'REAL_NETWORK');
    const tcpRecs = realRecs.filter(r => r.type === 'TCP' || r.type === 'TCP_VS_UDP_COMPARISON');
    const udpRecs = realRecs.filter(r => r.type === 'UDP' || r.type === 'TCP_VS_UDP_COMPARISON');

    // Throughput Chart
    const tpCtx = document.getElementById('dashboardThroughputChart');
    if (tpCtx) {
      this.destroy('dashboardThroughputChart');

      const labels = ['Recent TCP', 'Recent UDP'];
      const tcpLatest = tcpRecs[0] ? (tcpRecs[0].metrics.throughput_mbps || tcpRecs[0].metrics.tcp_throughput_mbps || 0) : 0;
      const udpLatest = udpRecs[0] ? (udpRecs[0].metrics.throughput_mbps || udpRecs[0].metrics.udp_throughput_mbps || 0) : 0;

      this.instances['dashboardThroughputChart'] = new Chart(tpCtx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: 'Throughput (Mbps)',
            data: [tcpLatest, udpLatest],
            backgroundColor: ['rgba(37, 99, 235, 0.8)', 'rgba(6, 182, 212, 0.8)'],
            borderColor: ['#2563eb', '#06b6d4'],
            borderWidth: 1,
            borderRadius: 6
          }]
        },
        options: {
          ...this.getChartDefaults(),
          plugins: {
            ...this.getChartDefaults().plugins,
            title: { display: true, text: 'Latest Measured Throughput (Mbps)', color: '#f1f5f9' }
          }
        }
      });
    }

    // Latency Chart
    const latCtx = document.getElementById('dashboardLatencyChart');
    if (latCtx) {
      this.destroy('dashboardLatencyChart');

      const tcpLatency = tcpRecs[0] ? (tcpRecs[0].metrics.avg_rtt_ms || tcpRecs[0].metrics.tcp_avg_rtt_ms || 0) : 0;
      const udpLatency = udpRecs[0] ? (udpRecs[0].metrics.avg_rtt_ms || udpRecs[0].metrics.udp_avg_rtt_ms || 0) : 0;

      this.instances['dashboardLatencyChart'] = new Chart(latCtx, {
        type: 'bar',
        data: {
          labels: ['TCP Average RTT', 'UDP Average RTT'],
          datasets: [{
            label: 'Avg Latency (ms)',
            data: [tcpLatency, udpLatency],
            backgroundColor: ['rgba(59, 130, 246, 0.7)', 'rgba(245, 158, 11, 0.7)'],
            borderColor: ['#3b82f6', '#f59e0b'],
            borderWidth: 1,
            borderRadius: 6
          }]
        },
        options: {
          ...this.getChartDefaults(),
          plugins: {
            ...this.getChartDefaults().plugins,
            title: { display: true, text: 'Round-Trip Latency (ms)', color: '#f1f5f9' }
          }
        }
      });
    }
  },

  // 2. TCP RTT Latency Per-Packet Chart
  renderTcpRttChart(packets) {
    if (!window.Chart) return;
    const ctx = document.getElementById('tcpRttChart');
    if (!ctx) return;
    this.destroy('tcpRttChart');

    const labels = packets.map(p => `#${p.seq}`);
    const rtts = packets.map(p => p.rtt_ms !== null ? p.rtt_ms : 0);

    this.instances['tcpRttChart'] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Round-Trip Time (ms)',
          data: rtts,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.15)',
          fill: true,
          tension: 0.2,
          pointRadius: 4,
          pointBackgroundColor: '#3b82f6'
        }]
      },
      options: {
        ...this.getChartDefaults(),
        plugins: {
          ...this.getChartDefaults().plugins,
          title: { display: true, text: 'TCP Round-Trip Time per Sequence (ms)', color: '#f1f5f9' }
        }
      }
    });
  },

  // 3. UDP RTT Latency Per-Packet Chart
  renderUdpRttChart(packets) {
    if (!window.Chart) return;
    const ctx = document.getElementById('udpRttChart');
    if (!ctx) return;
    this.destroy('udpRttChart');

    const labels = packets.map(p => `#${p.seq}`);
    const rtts = packets.map(p => p.rtt_ms !== null ? p.rtt_ms : null);

    this.instances['udpRttChart'] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'UDP RTT (ms) [Null indicates Timeout/Loss]',
          data: rtts,
          borderColor: '#06b6d4',
          backgroundColor: 'rgba(6, 182, 212, 0.15)',
          fill: true,
          tension: 0.2,
          spanGaps: false,
          pointRadius: 4,
          pointBackgroundColor: '#06b6d4'
        }]
      },
      options: {
        ...this.getChartDefaults(),
        plugins: {
          ...this.getChartDefaults().plugins,
          title: { display: true, text: 'UDP Round-Trip Time per Datagram (ms)', color: '#f1f5f9' }
        }
      }
    });
  },

  // 4. Comparison View Charts
  renderComparisonCharts(tcpMetrics, udpMetrics) {
    if (!window.Chart) return;
    const ctx = document.getElementById('comparisonThroughputChart');
    if (!ctx) return;
    this.destroy('comparisonThroughputChart');

    this.instances['comparisonThroughputChart'] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Throughput (Mbps)', 'Avg Latency (ms)', 'Delivery Ratio (%)'],
        datasets: [
          {
            label: 'TCP (Reliable Byte-Stream)',
            data: [tcpMetrics.throughput_mbps, tcpMetrics.avg_rtt_ms, tcpMetrics.delivery_ratio_pct],
            backgroundColor: 'rgba(37, 99, 235, 0.8)',
            borderColor: '#2563eb',
            borderWidth: 1,
            borderRadius: 6
          },
          {
            label: 'UDP (Unreliable Datagram)',
            data: [udpMetrics.throughput_mbps, udpMetrics.avg_rtt_ms, udpMetrics.delivery_ratio_pct],
            backgroundColor: 'rgba(6, 182, 212, 0.8)',
            borderColor: '#06b6d4',
            borderWidth: 1,
            borderRadius: 6
          }
        ]
      },
      options: {
        ...this.getChartDefaults(),
        plugins: {
          ...this.getChartDefaults().plugins,
          title: { display: true, text: 'Direct Side-by-Side Comparison', color: '#f1f5f9' }
        }
      }
    });
  },

  // 5. Leaky Bucket Chart
  renderLeakyBucketChart(chartData) {
    if (!window.Chart) return;
    const ctx = document.getElementById('leakyBucketChart');
    if (!ctx) return;
    this.destroy('leakyBucketChart');

    this.instances['leakyBucketChart'] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: chartData.labels,
        datasets: [
          {
            label: 'Incoming Packets',
            data: chartData.incoming,
            borderColor: '#f59e0b',
            backgroundColor: 'transparent',
            borderWidth: 2,
            stepped: true
          },
          {
            label: 'Transmitted (Leaked)',
            data: chartData.transmitted,
            borderColor: '#10b981',
            backgroundColor: 'transparent',
            borderWidth: 2
          },
          {
            label: 'Queue Depth',
            data: chartData.queue_size,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.2)',
            fill: true,
            borderWidth: 2
          },
          {
            label: 'Bucket Capacity Limit',
            data: chartData.capacity_line,
            borderColor: '#ef4444',
            borderDash: [5, 5],
            fill: false,
            pointRadius: 0
          }
        ]
      },
      options: {
        ...this.getChartDefaults(),
        plugins: {
          ...this.getChartDefaults().plugins,
          title: { display: true, text: 'Leaky Bucket Traffic Shaping Dynamics', color: '#f1f5f9' }
        }
      }
    });
  },

  // 6. Token Bucket Chart
  renderTokenBucketChart(chartData) {
    if (!window.Chart) return;
    const ctx = document.getElementById('tokenBucketChart');
    if (!ctx) return;
    this.destroy('tokenBucketChart');

    this.instances['tokenBucketChart'] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: chartData.labels,
        datasets: [
          {
            label: 'Incoming Packets',
            data: chartData.incoming,
            borderColor: '#f59e0b',
            borderWidth: 2,
            stepped: true
          },
          {
            label: 'Transmitted Packets (Bursts)',
            data: chartData.transmitted,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            fill: true,
            borderWidth: 2
          },
          {
            label: 'Tokens Remaining in Bucket',
            data: chartData.tokens_remaining,
            borderColor: '#8b5cf6',
            borderWidth: 2
          },
          {
            label: 'Queue Size',
            data: chartData.queue_size,
            borderColor: '#3b82f6',
            borderDash: [4, 4],
            fill: false
          }
        ]
      },
      options: {
        ...this.getChartDefaults(),
        plugins: {
          ...this.getChartDefaults().plugins,
          title: { display: true, text: 'Token Bucket Token Accumulation & Burst Transmissions', color: '#f1f5f9' }
        }
      }
    });
  },

  // 7. TCP Congestion Window Chart
  renderCongestionChart(chartData) {
    if (!window.Chart) return;
    const ctx = document.getElementById('congestionChart');
    if (!ctx) return;
    this.destroy('congestionChart');

    this.instances['congestionChart'] = new Chart(ctx, {
      type: 'line',
      data: {
        labels: chartData.rounds,
        datasets: [
          {
            label: 'Congestion Window (cwnd) [MSS]',
            data: chartData.cwnd,
            borderColor: '#06b6d4',
            backgroundColor: 'rgba(6, 182, 212, 0.18)',
            fill: true,
            borderWidth: 3,
            tension: 0.1,
            pointRadius: 5,
            pointBackgroundColor: '#06b6d4'
          },
          {
            label: 'Slow Start Threshold (ssthresh) [MSS]',
            data: chartData.ssthresh,
            borderColor: '#f59e0b',
            borderDash: [6, 4],
            borderWidth: 2,
            fill: false,
            pointRadius: 2
          }
        ]
      },
      options: {
        ...this.getChartDefaults(),
        plugins: {
          ...this.getChartDefaults().plugins,
          title: { display: true, text: 'TCP Reno Congestion Window Progression vs RTT Rounds', color: '#f1f5f9' }
        }
      }
    });
  }
};
