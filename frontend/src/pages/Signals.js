import React, { useState, useEffect } from 'react';
import { 
  Plus, 
  Upload, 
  Search, 
  Filter,
  Edit,
  Trash2,
  Play,
  AlertCircle,
  CheckCircle,
  Clock,
  RefreshCw
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { signalAPI, tradeAPI } from '../services/api';

const Signals = () => {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [showAddModal, setShowAddModal] = useState(false);
  const [showBatchModal, setShowBatchModal] = useState(false);
  const [newSignalText, setNewSignalText] = useState('');
  const [batchSignals, setBatchSignals] = useState('');
  const [pagination, setPagination] = useState({ page: 1, per_page: 20 });

  useEffect(() => {
    loadSignals();
  }, [pagination.page, filterStatus, searchTerm]);

  const loadSignals = async () => {
    try {
      setLoading(true);
      const params = {
        page: pagination.page,
        per_page: pagination.per_page,
        processed: filterStatus === 'all' ? undefined : filterStatus === 'processed',
        coin: searchTerm || undefined
      };

      const response = await signalAPI.getSignals(params);
      setSignals(response.data.signals || []);
      setPagination({ ...pagination, ...response.data.pagination });
    } catch (error) {
      console.error('Error loading signals:', error);
      toast.error('Failed to load signals');
    } finally {
      setLoading(false);
    }
  };

  const parseSignal = async () => {
    if (!newSignalText.trim()) {
      toast.error('Please enter signal text');
      return;
    }

    try {
      const response = await signalAPI.parseSignal(newSignalText);
      if (response.data.success) {
        toast.success('Signal parsed successfully');
        setNewSignalText('');
        setShowAddModal(false);
        loadSignals();
      } else {
        toast.error('Failed to parse signal');
      }
    } catch (error) {
      console.error('Error parsing signal:', error);
      toast.error('Error parsing signal');
    }
  };

  const batchParseSignals = async () => {
    if (!batchSignals.trim()) {
      toast.error('Please enter signals');
      return;
    }

    try {
      const signalTexts = batchSignals.split('\n\n').filter(s => s.trim());
      const response = await signalAPI.batchParseSignals(signalTexts);
      
      if (response.data.success) {
        toast.success(`Parsed ${response.data.signals_created} signals`);
        setBatchSignals('');
        setShowBatchModal(false);
        loadSignals();
      } else {
        toast.error('Failed to parse signals');
      }
    } catch (error) {
      console.error('Error batch parsing signals:', error);
      toast.error('Error parsing signals');
    }
  };

  const executeSignal = async (signalId) => {
    try {
      const response = await tradeAPI.executeSignal(signalId);
      if (response.data.success) {
        toast.success('Signal executed successfully');
        loadSignals();
      } else {
        toast.error(response.data.error || 'Failed to execute signal');
      }
    } catch (error) {
      console.error('Error executing signal:', error);
      toast.error('Error executing signal');
    }
  };

  const reparseSignal = async (signalId) => {
    try {
      const response = await signalAPI.reparseSignal(signalId);
      if (response.data.success) {
        toast.success('Signal reparsed successfully');
        loadSignals();
      } else {
        toast.error('Failed to reparse signal');
      }
    } catch (error) {
      console.error('Error reparsing signal:', error);
      toast.error('Error reparsing signal');
    }
  };

  const deleteSignal = async (signalId) => {
    if (!window.confirm('Are you sure you want to delete this signal?')) {
      return;
    }

    try {
      await signalAPI.deleteSignal(signalId);
      toast.success('Signal deleted successfully');
      loadSignals();
    } catch (error) {
      console.error('Error deleting signal:', error);
      toast.error('Error deleting signal');
    }
  };

  const getStatusIcon = (signal) => {
    if (signal.processed) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    } else if (signal.parse_errors?.length > 0) {
      return <AlertCircle className="w-5 h-5 text-red-500" />;
    } else {
      return <Clock className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusText = (signal) => {
    if (signal.processed) return 'Processed';
    if (signal.parse_errors?.length > 0) return 'Parse Error';
    return 'Pending';
  };

  const filteredSignals = signals.filter(signal => {
    const matchesSearch = !searchTerm || 
      (signal.coin && signal.coin.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesFilter = 
      filterStatus === 'all' ||
      (filterStatus === 'processed' && signal.processed) ||
      (filterStatus === 'pending' && !signal.processed && !signal.parse_errors?.length) ||
      (filterStatus === 'errors' && signal.parse_errors?.length > 0);

    return matchesSearch && matchesFilter;
  });

  return (
    <div className="space-y-6 fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Signals</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage and parse Telegram trading signals
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowBatchModal(true)}
            className="btn-secondary flex items-center space-x-2"
          >
            <Upload className="w-4 h-4" />
            <span>Batch Import</span>
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="btn-primary flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Add Signal</span>
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card p-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0 md:space-x-4">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search by coin..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10 input-field"
              />
            </div>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="input-field"
            >
              <option value="all">All Signals</option>
              <option value="processed">Processed</option>
              <option value="pending">Pending</option>
              <option value="errors">Parse Errors</option>
            </select>
          </div>
          <button
            onClick={loadSignals}
            className="btn-secondary flex items-center space-x-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Signals List */}
      <div className="card">
        {loading ? (
          <div className="flex items-center justify-center p-8">
            <div className="loading-spinner w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
          </div>
        ) : filteredSignals.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 dark:text-gray-400">No signals found</p>
          </div>
        ) : (
          <div className="table-container">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Coin
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Position
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Entry Zones
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Targets
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Leverage
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredSignals.map((signal) => (
                  <tr key={signal.id} className="table-row">
                    <td className="px-6 py-4">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(signal)}
                        <span className="text-sm font-medium">
                          {getStatusText(signal)}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-gray-900 dark:text-white">
                        {signal.coin || 'N/A'}/{signal.pair}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        signal.position_type === 'LONG' 
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : signal.position_type === 'SHORT'
                          ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                          : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
                      }`}>
                        {signal.position_type || 'N/A'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 dark:text-white">
                        {signal.entry_zones?.length > 0 
                          ? signal.entry_zones.slice(0, 2).map(zone => zone.toFixed(4)).join(', ')
                          : 'N/A'
                        }
                        {signal.entry_zones?.length > 2 && '...'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900 dark:text-white">
                        {signal.targets?.length > 0 
                          ? signal.targets.slice(0, 2).map(target => target.toFixed(4)).join(', ')
                          : 'N/A'
                        }
                        {signal.targets?.length > 2 && '...'}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-sm text-gray-900 dark:text-white">
                        {signal.leverage}x
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-500 dark:text-gray-400">
                        {new Date(signal.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        {!signal.processed && signal.coin && (
                          <button
                            onClick={() => executeSignal(signal.id)}
                            className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                            title="Execute Trade"
                          >
                            <Play className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => reparseSignal(signal.id)}
                          className="text-yellow-600 hover:text-yellow-900 dark:text-yellow-400 dark:hover:text-yellow-300"
                          title="Reparse Signal"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => deleteSignal(signal.id)}
                          className="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300"
                          title="Delete Signal"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Signal Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl mx-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Add New Signal
            </h3>
            <textarea
              value={newSignalText}
              onChange={(e) => setNewSignalText(e.target.value)}
              placeholder="Paste your Telegram signal here..."
              className="w-full h-40 input-field resize-none font-mono"
              rows={8}
            />
            <div className="flex justify-end space-x-3 mt-4">
              <button
                onClick={() => setShowAddModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={parseSignal}
                className="btn-primary"
              >
                Parse Signal
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Batch Import Modal */}
      {showBatchModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-4xl mx-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Batch Import Signals
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Separate multiple signals with double line breaks (empty line between signals)
            </p>
            <textarea
              value={batchSignals}
              onChange={(e) => setBatchSignals(e.target.value)}
              placeholder="Signal 1 here...

Signal 2 here...

Signal 3 here..."
              className="w-full h-60 input-field resize-none font-mono"
              rows={15}
            />
            <div className="flex justify-end space-x-3 mt-4">
              <button
                onClick={() => setShowBatchModal(false)}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                onClick={batchParseSignals}
                className="btn-primary"
              >
                Import Signals
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Signals;