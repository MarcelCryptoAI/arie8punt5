import React, { useState, useEffect } from 'react';
import { Brain, Zap, TrendingUp, Settings } from 'lucide-react';
import { toast } from 'react-hot-toast';
import { aiAPI } from '../services/api';

const AIOptimization = () => {
  const [optimizations, setOptimizations] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [optimizationsResponse, suggestionsResponse] = await Promise.all([
        aiAPI.getOptimizations({ per_page: 5 }),
        aiAPI.getSuggestions()
      ]);

      setOptimizations(optimizationsResponse.data.optimizations || []);
      setSuggestions(suggestionsResponse.data.suggestions || []);
    } catch (error) {
      console.error('Error loading AI data:', error);
      toast.error('Failed to load AI optimization data');
    } finally {
      setLoading(false);
    }
  };

  const runOptimization = async () => {
    try {
      const response = await aiAPI.optimizeSettings();
      if (response.data.success) {
        toast.success('AI optimization completed');
        loadData();
      }
    } catch (error) {
      console.error('Error running optimization:', error);
      toast.error('Failed to run AI optimization');
    }
  };

  const applyOptimization = async (id) => {
    try {
      await aiAPI.applyOptimization(id);
      toast.success('Optimization applied successfully');
      loadData();
    } catch (error) {
      console.error('Error applying optimization:', error);
      toast.error('Failed to apply optimization');
    }
  };

  return (
    <div className="space-y-6 fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">AI Optimization</h1>
          <p className="text-gray-600 dark:text-gray-400">
            AI-powered strategy improvements and recommendations
          </p>
        </div>
        <button
          onClick={runOptimization}
          className="btn-primary flex items-center space-x-2"
        >
          <Brain className="w-4 h-4" />
          <span>Run AI Analysis</span>
        </button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center p-8">
          <div className="loading-spinner w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* AI Suggestions */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <Brain className="w-5 h-5 mr-2 text-blue-500" />
              AI Suggestions
            </h3>
            <div className="space-y-3">
              {suggestions.length > 0 ? suggestions.map((suggestion, index) => (
                <div key={index} className="ai-suggestion p-4 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900 dark:text-white">
                        {suggestion.title}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {suggestion.description}
                      </p>
                      <span className={`inline-block mt-2 px-2 py-1 text-xs rounded-full ${
                        suggestion.priority === 'high' ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200' :
                        suggestion.priority === 'medium' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200' :
                        'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                      }`}>
                        {suggestion.priority} priority
                      </span>
                    </div>
                  </div>
                </div>
              )) : (
                <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                  No AI suggestions available. Run analysis to get recommendations.
                </p>
              )}
            </div>
          </div>

          {/* Recent Optimizations */}
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
              <TrendingUp className="w-5 h-5 mr-2 text-green-500" />
              Recent Optimizations
            </h3>
            <div className="space-y-3">
              {optimizations.length > 0 ? optimizations.map((optimization) => (
                <div key={optimization.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {optimization.optimization_type}
                        </span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {new Date(optimization.created_at).toLocaleDateString()}
                        </span>
                      </div>
                      <div className="mt-2 flex items-center space-x-4">
                        <span className="text-sm text-gray-600 dark:text-gray-400">
                          Confidence: {(optimization.confidence_score * 100).toFixed(0)}%
                        </span>
                        <span className="text-sm text-green-600 dark:text-green-400">
                          Expected: +{optimization.expected_improvement?.toFixed(1)}%
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {!optimization.applied && (
                        <button
                          onClick={() => applyOptimization(optimization.id)}
                          className="btn-primary text-xs flex items-center space-x-1"
                        >
                          <Zap className="w-3 h-3" />
                          <span>Apply</span>
                        </button>
                      )}
                      {optimization.applied && (
                        <span className="text-xs text-green-600 dark:text-green-400 font-medium">
                          Applied
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              )) : (
                <p className="text-gray-500 dark:text-gray-400 text-center py-4">
                  No optimizations found. Run AI analysis to generate recommendations.
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* AI Configuration */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center">
          <Settings className="w-5 h-5 mr-2 text-gray-500" />
          AI Configuration
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">OpenAI</div>
            <div className="text-sm text-gray-500 dark:text-gray-400">AI Provider</div>
          </div>
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">Enabled</div>
            <div className="text-sm text-gray-500 dark:text-gray-400">AI Status</div>
          </div>
          <div className="text-center p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <div className="text-2xl font-bold text-purple-600 dark:text-purple-400">GPT-4</div>
            <div className="text-sm text-gray-500 dark:text-gray-400">Model</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AIOptimization;