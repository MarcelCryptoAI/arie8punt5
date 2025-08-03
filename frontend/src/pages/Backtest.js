import React, { useState, useEffect } from 'react';
import { Play, Plus, BarChart3, FileText } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { backtestAPI } from '../services/api';

const Backtest = () => {
  const [backtests, setBacktests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newBacktest, setNewBacktest] = useState({
    name: '',
    signals: '',
    initial_balance: 1000
  });

  useEffect(() => {
    loadBacktests();
  }, []);

  const loadBacktests = async () => {
    try {
      setLoading(true);
      const response = await backtestAPI.getBacktests();
      setBacktests(response.data.backtests || []);
    } catch (error) {
      console.error('Error loading backtests:', error);
      toast.error('Failed to load backtests');
    } finally {
      setLoading(false);
    }
  };

  const createBacktest = async () => {
    if (!newBacktest.name || !newBacktest.signals) {
      toast.error('Please fill in all fields');
      return;
    }

    try {
      const signalTexts = newBacktest.signals.split('\n\n').filter(s => s.trim());
      const response = await backtestAPI.createBacktest({
        name: newBacktest.name,
        signals: signalTexts,
        initial_balance: newBacktest.initial_balance
      });

      if (response.data.success) {
        toast.success('Backtest created successfully');
        setShowCreateModal(false);
        setNewBacktest({ name: '', signals: '', initial_balance: 1000 });
        loadBacktests();
      }
    } catch (error) {
      console.error('Error creating backtest:', error);
      toast.error('Failed to create backtest');
    }
  };

  const runBacktest = async (id) => {
    try {
      await backtestAPI.runBacktest(id);
      toast.success('Backtest started');
      loadBacktests();
    } catch (error) {
      console.error('Error running backtest:', error);
      toast.error('Failed to run backtest');
    }
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Backtest</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Test your strategies with historical data
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <Plus className="w-4 h-4" />
          <span>New Backtest</span>
        </button>
      </div>

      {/* Backtests List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full flex items-center justify-center p-8">
            <div className="loading-spinner w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        ) : backtests.length === 0 ? (
          <div className="col-span-full text-center py-8">
            <p className="text-gray-500 dark:text-gray-400">No backtests found</p>
          </div>
        ) : (
          backtests.map((backtest) => (
            <div key={backtest.id} className="card p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {backtest.name}
                </h3>
                <span className={`status-badge ${
                  backtest.status === 'completed' ? 'status-completed' :
                  backtest.status === 'running' ? 'status-active' :
                  backtest.status === 'failed' ? 'status-failed' : 'status-pending'
                }`}>
                  {backtest.status}
                </span>
              </div>
              
              {backtest.status === 'completed' && (
                <div className="space-y-2 mb-4">
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500 dark:text-gray-400">P&L:</span>
                    <span className={`text-sm font-medium ${
                      backtest.total_pnl_percentage > 0 ? 'pnl-positive' : 'pnl-negative'
                    }`}>
                      {backtest.total_pnl_percentage > 0 ? '+' : ''}{backtest.total_pnl_percentage?.toFixed(2)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500 dark:text-gray-400">Win Rate:</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {backtest.win_rate?.toFixed(1)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-500 dark:text-gray-400">Trades:</span>
                    <span className="text-sm font-medium text-gray-900 dark:text-white">
                      {backtest.total_trades}
                    </span>
                  </div>
                </div>
              )}

              <div className="flex space-x-2">
                {backtest.status === 'pending' && (
                  <button
                    onClick={() => runBacktest(backtest.id)}
                    className="btn-primary flex items-center space-x-1 text-xs"
                  >
                    <Play className="w-3 h-3" />
                    <span>Run</span>
                  </button>
                )}
                <button className="btn-secondary flex items-center space-x-1 text-xs">
                  <BarChart3 className="w-3 h-3" />
                  <span>View</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl mx-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Create New Backtest
            </h3>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Backtest name"
                value={newBacktest.name}
                onChange={(e) => setNewBacktest({...newBacktest, name: e.target.value})}
                className="input-field"
              />
              <input
                type="number"
                placeholder="Initial balance (USDT)"
                value={newBacktest.initial_balance}
                onChange={(e) => setNewBacktest({...newBacktest, initial_balance: Number(e.target.value)})}
                className="input-field"
              />
              <textarea
                placeholder="Paste signals here (separate with double line breaks)"
                value={newBacktest.signals}
                onChange={(e) => setNewBacktest({...newBacktest, signals: e.target.value})}
                className="input-field h-32 resize-none font-mono"
              />
            </div>
            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={createBacktest}
                className="btn-primary"
              >
                Create Backtest
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Backtest;