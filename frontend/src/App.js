import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navbar from './components/Layout/Navbar';
import Sidebar from './components/Layout/Sidebar';
import Dashboard from './pages/Dashboard';
import Signals from './pages/Signals';
import Trades from './pages/Trades';
import Backtest from './pages/Backtest';
import AIOptimization from './pages/AIOptimization';
import Settings from './pages/Settings';
import './App.css';

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Toaster 
          position="top-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#363636',
              color: '#fff',
            },
          }}
        />
        
        <Navbar />
        
        <div className="flex">
          <Sidebar />
          
          <main className="flex-1 ml-64 p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/signals" element={<Signals />} />
              <Route path="/trades" element={<Trades />} />
              <Route path="/backtest" element={<Backtest />} />
              <Route path="/ai" element={<AIOptimization />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}

export default App;