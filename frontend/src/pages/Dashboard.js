import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Activity, 
  DollarSign, 
  Target,
  AlertCircle,
  CheckCircle,
  Clock
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { tradeAPI, signalAPI, settingsAPI } from '../services/api';

const Dashboard = () => {
  const [stats, setStats] = useState({
    totalTrades: 0,
    activeTrades: 0,
    totalPnL: 0,
    winRate: 0,
    todayPnL: 0
  });
  const [recentTrades, setRecentTrades] = useState([]);
  const [recentSignals, setRecentSignals] = useState([]);
  const [equityData, setEquityData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load parallel data
      const [tradesResponse, signalsResponse, tradeStatsResponse] = await Promise.all([
        tradeAPI.getTrades({ per_page: 5 }),
        signalAPI.getSignals({ per_page: 5 }),
        tradeAPI.getTradeStats()
      ]);

      setRecentTrades(tradesResponse.data.trades || []);
      setRecentSignals(signalsResponse.data.signals || []);
      setStats({
        totalTrades: tradeStatsResponse.data.total_trades || 0,
        activeTrades: tradeStatsResponse.data.active_trades || 0,
        totalPnL: tradeStatsResponse.data.total_pnl || 0,
        winRate: tradeStatsResponse.data.win_rate || 0,
        todayPnL: tradeStatsResponse.data.total_pnl || 0 // Simplified for demo
      });

      // Generate sample equity curve data
      setEquityData(generateEquityData());

    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateEquityData = () => {
    const data = [];
    let balance = 1000;
    for (let i = 0; i < 30; i++) {
      balance += (Math.random() - 0.45) * 20; // Slight upward trend
      data.push({
        date: new Date(Date.now() - (29 - i) * 24 * 60 * 60 * 1000).toLocaleDateString(),
        balance: Math.round(balance * 100) / 100
      });
    }
    return data;
  };

  const StatCard = ({ title, value, change, icon: Icon, color = 'blue' }) => (
    <div className="card p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
          {change && (
            <p className={`text-sm ${change >= 0 ? 'text-green-600' : 'text-red-600'} flex items-center mt-1`}>
              {change >= 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
              {Math.abs(change)}%
            </p>
          )}
        </div>
        <div className={`p-3 rounded-full bg-${color}-100 dark:bg-${color}-900`}>
          <Icon className={`w-6 h-6 text-${color}-600 dark:text-${color}-400`} />
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard CLEAN v393</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Overview of your trading bot performance
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-2 px-3 py-1 bg-green-100 dark:bg-green-900 rounded-full">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-green-800 dark:text-green-200">
              Bot Active
            </span>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total P&L"
          value={`$${stats.totalPnL.toFixed(2)}`}
          change={12.5}
          icon={DollarSign}
          color="green"
        />
        <StatCard
          title="Active Trades"
          value={stats.activeTrades}
          icon={Activity}
          color="blue"
        />
        <StatCard
          title="Win Rate"
          value={`${stats.winRate}%`}
          change={2.3}
          icon={Target}
          color="purple"
        />
        <StatCard
          title="Total Trades"
          value={stats.totalTrades}
          icon={TrendingUp}
          color="indigo"
        />
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Equity Curve */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Account Equity (30 Days)
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={equityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="balance" stroke="#3b82f6" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Performance Overview */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Weekly Performance
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={[
                { day: 'Mon', pnl: 45 },
                { day: 'Tue', pnl: -23 },
                { day: 'Wed', pnl: 78 },
                { day: 'Thu', pnl: 34 },
                { day: 'Fri', pnl: -12 },
                { day: 'Sat', pnl: 56 },
                { day: 'Sun', pnl: 23 }
              ]}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="pnl" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Trades */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Recent Trades
          </h3>
          <div className="space-y-3">
            {recentTrades.length > 0 ? recentTrades.map((trade) => (
              <div key={trade.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`w-3 h-3 rounded-full ${
                    trade.status === 'active' ? 'bg-blue-500' :
                    trade.status === 'closed' ? 'bg-green-500' : 'bg-gray-400'
                  }`}></div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {trade.coin}/{trade.pair} {trade.position_type}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {trade.leverage}x leverage
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-medium ${
                    trade.pnl > 0 ? 'text-green-600' : 
                    trade.pnl < 0 ? 'text-red-600' : 'text-gray-600'
                  }`}>
                    {trade.pnl > 0 ? '+' : ''}${trade.pnl?.toFixed(2) || '0.00'}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {trade.status}
                  </p>
                </div>
              </div>
            )) : (
              <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                No recent trades
              </p>
            )}
          </div>
        </div>

        {/* Recent Signals */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Recent Signals
          </h3>
          <div className="space-y-3">
            {recentSignals.length > 0 ? recentSignals.map((signal) => (
              <div key={signal.id} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                <div className="flex items-center space-x-3">
                  {signal.processed ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : signal.parse_errors?.length > 0 ? (
                    <AlertCircle className="w-5 h-5 text-red-500" />
                  ) : (
                    <Clock className="w-5 h-5 text-yellow-500" />
                  )}
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">
                      {signal.coin || 'Unknown'}/{signal.pair} {signal.position_type || 'N/A'}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {signal.leverage}x leverage
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-medium ${
                    signal.processed ? 'text-green-600' :
                    signal.parse_errors?.length > 0 ? 'text-red-600' : 'text-yellow-600'
                  }`}>
                    {signal.processed ? 'Processed' :
                     signal.parse_errors?.length > 0 ? 'Parse Error' : 'Pending'}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {new Date(signal.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </div>
            )) : (
              <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                No recent signals
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;