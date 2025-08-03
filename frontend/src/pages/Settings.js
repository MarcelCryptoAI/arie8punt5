import React, { useState, useEffect } from 'react';
import { 
  Save, 
  TestTube, 
  Download, 
  Upload, 
  RotateCcw,
  CheckCircle,
  XCircle,
  Key
} from 'lucide-react';
import { toast } from 'react-hot-toast';
import { settingsAPI } from '../services/api';

const Settings = () => {
  const [settings, setSettings] = useState({});
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState(null);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await settingsAPI.getSettings();
      setSettings(response.data);
    } catch (error) {
      console.error('Error loading settings:', error);
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const saveSettings = async () => {
    try {
      await settingsAPI.updateSettings(settings);
      toast.success('Settings saved successfully');
    } catch (error) {
      console.error('Error saving settings:', error);
      toast.error('Failed to save settings');
    }
  };

  const testConnection = async () => {
    setTesting(true);
    try {
      const response = await settingsAPI.testConnection();
      if (response.data.success) {
        setConnectionStatus('success');
        toast.success('API connection successful');
      } else {
        setConnectionStatus('error');
        toast.error('API connection failed');
      }
    } catch (error) {
      setConnectionStatus('error');
      toast.error('API connection failed');
    } finally {
      setTesting(false);
    }
  };

  const updateSetting = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value
    }));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loading-spinner w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Settings</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Configure your trading bot parameters and API connections
          </p>
        </div>
        <button
          onClick={saveSettings}
          className="btn-primary flex items-center space-x-2"
        >
          <Save className="w-4 h-4" />
          <span>Save Settings</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* API Configuration */}
        <div className="card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center">
              <Key className="w-5 h-5 mr-2 text-blue-500" />
              Bitunix API Configuration
            </h3>
            <div className="flex items-center space-x-2">
              {connectionStatus === 'success' && (
                <CheckCircle className="w-5 h-5 text-green-500" />
              )}
              {connectionStatus === 'error' && (
                <XCircle className="w-5 h-5 text-red-500" />
              )}
              <button
                onClick={testConnection}
                disabled={testing}
                className="btn-secondary text-sm flex items-center space-x-1"
              >
                <TestTube className="w-3 h-3" />
                <span>{testing ? 'Testing...' : 'Test'}</span>
              </button>
            </div>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                API Key
              </label>
              <input
                type="password"
                value={settings.api_key || ''}
                onChange={(e) => updateSetting('api_key', e.target.value)}
                placeholder="Enter your Bitunix API key"
                className="input-field"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                API Secret
              </label>
              <input
                type="password"
                value={settings.api_secret || ''}
                onChange={(e) => updateSetting('api_secret', e.target.value)}
                placeholder="Enter your Bitunix API secret"
                className="input-field"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                API Passphrase
              </label>
              <input
                type="password"
                value={settings.api_passphrase || ''}
                onChange={(e) => updateSetting('api_passphrase', e.target.value)}
                placeholder="Enter your Bitunix API passphrase"
                className="input-field"
              />
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                id="testnet"
                checked={settings.testnet || false}
                onChange={(e) => updateSetting('testnet', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
              />
              <label htmlFor="testnet" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Use Testnet
              </label>
            </div>
          </div>
        </div>

        {/* Trading Configuration */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Trading Configuration
          </h3>
          
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Default Leverage
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={settings.default_leverage || 1}
                  onChange={(e) => updateSetting('default_leverage', Number(e.target.value))}
                  className="input-field"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Risk Percentage (%)
                </label>
                <input
                  type="number"
                  min="0.1"
                  max="10"
                  step="0.1"
                  value={settings.risk_percentage || 2}
                  onChange={(e) => updateSetting('risk_percentage', Number(e.target.value))}
                  className="input-field"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Default Position Size (USDT)
                </label>
                <input
                  type="number"
                  min="10"
                  value={settings.default_position_size || 10}
                  onChange={(e) => updateSetting('default_position_size', Number(e.target.value))}
                  className="input-field"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Entry Steps
                </label>
                <input
                  type="number"
                  min="1"
                  max="5"
                  value={settings.entry_steps || 3}
                  onChange={(e) => updateSetting('entry_steps', Number(e.target.value))}
                  className="input-field"
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="auto_trade"
                  checked={settings.auto_trade || false}
                  onChange={(e) => updateSetting('auto_trade', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                />
                <label htmlFor="auto_trade" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Auto Trading
                </label>
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="auto_stop_loss"
                  checked={settings.auto_stop_loss || false}
                  onChange={(e) => updateSetting('auto_stop_loss', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                />
                <label htmlFor="auto_stop_loss" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Auto Stop Loss
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* AI Configuration */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            AI Configuration
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                AI Provider
              </label>
              <select
                value={settings.ai_provider || 'openai'}
                onChange={(e) => updateSetting('ai_provider', e.target.value)}
                className="input-field"
              >
                <option value="openai">OpenAI</option>
                <option value="anthropic">Anthropic</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                AI Model
              </label>
              <select
                value={settings.ai_model || 'gpt-4'}
                onChange={(e) => updateSetting('ai_model', e.target.value)}
                className="input-field"
              >
                <option value="gpt-4">GPT-4</option>
                <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                <option value="claude-3-sonnet">Claude 3 Sonnet</option>
              </select>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="ai_enabled"
                  checked={settings.ai_enabled || false}
                  onChange={(e) => updateSetting('ai_enabled', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                />
                <label htmlFor="ai_enabled" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Enable AI
                </label>
              </div>
              
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="auto_optimize"
                  checked={settings.auto_optimize || false}
                  onChange={(e) => updateSetting('auto_optimize', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
                />
                <label htmlFor="auto_optimize" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                  Auto Optimize
                </label>
              </div>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Notifications
          </h3>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Email Address
              </label>
              <input
                type="email"
                value={settings.email_address || ''}
                onChange={(e) => updateSetting('email_address', e.target.value)}
                placeholder="Enter your email address"
                className="input-field"
              />
            </div>
            
            <div className="flex items-center">
              <input
                type="checkbox"
                id="email_notifications"
                checked={settings.email_notifications || false}
                onChange={(e) => updateSetting('email_notifications', e.target.checked)}
                className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50"
              />
              <label htmlFor="email_notifications" className="ml-2 text-sm text-gray-700 dark:text-gray-300">
                Enable Email Notifications
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;