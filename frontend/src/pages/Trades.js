import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  X, 
  RefreshCw,
  Play,
  Square
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { tradeAPI } from '../services/api';

const Trades = () => {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('active');

  useEffect(() => {
    loadTrades();
  }, [activeTab]);

  const loadTrades = async () => {
    try {
      setLoading(true);
      let response;
      
      if (activeTab === 'active') {
        response = await tradeAPI.getActiveTrades();
      } else {
        response = await tradeAPI.getTradeHistory();
      }
      
      setTrades(response.data.trades || []);
    } catch (error) {
      console.error('Error loading trades:', error);
      toast.error('Failed to load trades');
    } finally {
      setLoading(false);
    }
  };

  const closeTrade = async (tradeId) => {
    if (!window.confirm('Are you sure you want to close this trade?')) return;
    
    try {
      await tradeAPI.closeTrade(tradeId);
      toast.success('Trade closed successfully');
      loadTrades();
    } catch (error) {
      console.error('Error closing trade:', error);
      toast.error('Failed to close trade');
    }
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Trades</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your active and historical trades
          </p>
        </div>
        <button onClick={loadTrades} className="btn-secondary flex items-center space-x-2">
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'active', name: 'Active Trades', icon: Play },
            { id: 'history', name: 'Trade History', icon: Square }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span>{tab.name}</span>
            </button>
          ))}
        </nav>
      </div>

      {/* Trades List */}
      <div className="card">
        {loading ? (
          <div className="flex items-center justify-center p-8">
            <div className="loading-spinner w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        ) : trades.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 dark:text-gray-400">
              No {activeTab} trades found
            </p>
          </div>
        ) : (
          <div className="table-container">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Coin
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Position
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Entry Price
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Size
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    P&L
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {trades.map((trade) => (
                  <tr key={trade.id} className="table-row">
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900 dark:text-white">
                        {trade.coin}/{trade.pair}
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {trade.leverage}x leverage
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        trade.position_type === 'LONG' 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                      }`}>
                        {trade.position_type === 'LONG' ? (
                          <TrendingUp className="w-3 h-3 mr-1" />
                        ) : (
                          <TrendingDown className="w-3 h-3 mr-1" />
                        )}
                        {trade.position_type}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                      ${trade.entry_price?.toFixed(4) || 'N/A'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 dark:text-white">
                      ${trade.size?.toFixed(2) || 'N/A'}
                    </td>
                    <td className="px-6 py-4">
                      <div className={`text-sm font-medium ${
                        trade.pnl > 0 ? 'pnl-positive' : trade.pnl < 0 ? 'pnl-negative' : 'text-gray-500'
                      }`}>
                        {trade.pnl > 0 ? '+' : ''}${trade.pnl?.toFixed(2) || '0.00'}
                      </div>
                      <div className={`text-xs ${
                        trade.pnl_percentage > 0 ? 'pnl-positive' : trade.pnl_percentage < 0 ? 'pnl-negative' : 'text-gray-500'
                      }`}>
                        {trade.pnl_percentage > 0 ? '+' : ''}{trade.pnl_percentage?.toFixed(2) || '0.00'}%
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`status-badge ${
                        trade.status === 'active' ? 'status-active' :
                        trade.status === 'closed' ? 'status-completed' :
                        trade.status === 'pending' ? 'status-pending' : 'status-failed'
                      }`}>
                        {trade.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right">
                      {trade.status === 'active' && (
                        <button
                          onClick={() => closeTrade(trade.id)}
                          className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                          title="Close Trade"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Trades;