import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: process.env.NODE_ENV === 'production' 
    ? 'https://arietelegram-1d3bfa587442.herokuapp.com/api' 
    : '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens if needed
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for handling errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      // Request was made but no response
      console.error('Network Error:', error.request);
    } else {
      // Something else happened
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Signal API endpoints
export const signalAPI = {
  getSignals: (params = {}) => api.get('/signals', { params }),
  getSignal: (id) => api.get(`/signals/${id}`),
  parseSignal: (text) => api.post('/signals/parse', { text }),
  batchParseSignals: (signals) => api.post('/signals/batch-parse', { signals }),
  updateSignal: (id, data) => api.put(`/signals/${id}`, data),
  deleteSignal: (id) => api.delete(`/signals/${id}`),
  reparseSignal: (id) => api.post(`/signals/reparse/${id}`),
  getSignalStats: () => api.get('/signals/stats'),
};

// Trade API endpoints
export const tradeAPI = {
  getTrades: (params = {}) => api.get('/trades', { params }),
  getTrade: (id) => api.get(`/trades/${id}`),
  executeSignal: (signalId) => api.post(`/trades/execute/${signalId}`),
  updateTradeStatus: (id) => api.post(`/trades/${id}/update`),
  closeTrade: (id) => api.post(`/trades/${id}/close`),
  getActiveTrades: () => api.get('/trades/active'),
  getTradeHistory: (days = 30) => api.get('/trades/history', { params: { days } }),
  getTradeStats: () => api.get('/trades/stats'),
};

// Settings API endpoints
export const settingsAPI = {
  getSettings: () => api.get('/settings'),
  updateSettings: (data) => api.put('/settings', data),
  testConnection: () => api.post('/settings/test-connection'),
  getPresets: () => api.get('/settings/presets'),
  applyPreset: (presetName) => api.post(`/settings/presets/${presetName}`),
  backupSettings: () => api.get('/settings/backup'),
  restoreSettings: (backup) => api.post('/settings/restore', { backup }),
  resetSettings: () => api.post('/settings/reset'),
};

// Backtest API endpoints
export const backtestAPI = {
  getBacktests: (params = {}) => api.get('/backtest', { params }),
  getBacktest: (id) => api.get(`/backtest/${id}`),
  createBacktest: (data) => api.post('/backtest/create', data),
  runBacktest: (id) => api.post(`/backtest/${id}/run`),
  deleteBacktest: (id) => api.delete(`/backtest/${id}`),
  compareBacktests: (backtestIds) => api.post('/backtest/compare', { backtest_ids: backtestIds }),
  getTemplateSignals: () => api.get('/backtest/template'),
  getBacktestStats: () => api.get('/backtest/stats'),
};

// AI API endpoints
export const aiAPI = {
  getOptimizations: (params = {}) => api.get('/ai/optimizations', { params }),
  getOptimization: (id) => api.get(`/ai/optimizations/${id}`),
  analyzeBacktest: (backtestId, type = 'parameters') => 
    api.post(`/ai/analyze-backtest/${backtestId}`, { type }),
  optimizeSettings: (goals = ['maximize_profit', 'minimize_drawdown']) => 
    api.post('/ai/optimize-settings', { goals }),
  applyOptimization: (id) => api.post(`/ai/optimizations/${id}/apply`),
  getSuggestions: () => api.get('/ai/suggestions'),
  analyzeMarketConditions: (coins = ['BTC', 'ETH', 'SOL']) => 
    api.post('/ai/market-analysis', { coins }),
  getAIStats: () => api.get('/ai/stats'),
};

// Health check endpoint
export const healthAPI = {
  check: () => api.get('/health'),
  status: () => api.get('/'),
};

// Export default api instance
export default api;