/**
 * REST API Client for TCP/UDP Performance Analyzer
 */
const API = {
  async get(endpoint) {
    try {
      const res = await fetch(endpoint);
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: res.statusText }));
        throw new Error(err.error || `HTTP error ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      console.error(`API GET ${endpoint} failed:`, err);
      throw err;
    }
  },

  async post(endpoint, data = {}) {
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: res.statusText }));
        throw new Error(err.error || `HTTP error ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      console.error(`API POST ${endpoint} failed:`, err);
      throw err;
    }
  },

  async delete(endpoint) {
    try {
      const res = await fetch(endpoint, { method: 'DELETE' });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: res.statusText }));
        throw new Error(err.error || `HTTP error ${res.status}`);
      }
      return await res.json();
    } catch (err) {
      console.error(`API DELETE ${endpoint} failed:`, err);
      throw err;
    }
  },

  // Servers
  getServerStatus() {
    return this.get('/api/servers/status');
  },
  startTcpServer(port) {
    return this.post('/api/servers/tcp/start', { port });
  },
  stopTcpServer() {
    return this.post('/api/servers/tcp/stop');
  },
  startUdpServer(port, simulatedLoss = 0.0) {
    return this.post('/api/servers/udp/start', { port, simulate_loss_rate: simulatedLoss });
  },
  stopUdpServer() {
    return this.post('/api/servers/udp/stop');
  },

  // Experiments
  runTcpExperiment(config) {
    return this.post('/api/tcp/start', config);
  },
  runUdpExperiment(config) {
    return this.post('/api/udp/start', config);
  },
  runComparison(config) {
    return this.post('/api/compare/run', config);
  },

  // Algorithms
  simulateLeakyBucket(config) {
    return this.post('/api/leaky-bucket/simulate', config);
  },
  simulateTokenBucket(config) {
    return this.post('/api/token-bucket/simulate', config);
  },
  compareTrafficShaping(config) {
    return this.post('/api/shaping/compare', config);
  },
  simulateCongestion(config) {
    return this.post('/api/congestion/simulate', config);
  },

  // History & Stats
  getDashboardStats() {
    return this.get('/api/dashboard/stats');
  },
  getExperiments(limit = 50) {
    return this.get(`/api/experiments?limit=${limit}`);
  },
  getExperimentDetail(id) {
    return this.get(`/api/experiments/${id}`);
  },
  clearHistory() {
    return this.delete('/api/experiments/clear');
  },
  getExportUrl() {
    return '/api/experiments/export';
  }
};
