import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Radio,
  TrendingUp,
  BarChart3,
  Brain,
  Settings,
  FileText,
  Target
} from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();

  const navigation = [
    {
      name: 'Dashboard',
      href: '/',
      icon: LayoutDashboard,
      description: 'Overview and live status'
    },
    {
      name: 'Signals',
      href: '/signals',
      icon: Radio,
      description: 'Telegram signal parsing'
    },
    {
      name: 'Trades',
      href: '/trades',
      icon: TrendingUp,
      description: 'Active and historical trades'
    },
    {
      name: 'Backtest',
      href: '/backtest',
      icon: BarChart3,
      description: 'Strategy backtesting'
    },
    {
      name: 'AI Optimization',
      href: '/ai',
      icon: Brain,
      description: 'AI-powered improvements'
    },
    {
      name: 'Settings',
      href: '/settings',
      icon: Settings,
      description: 'Configuration and API keys'
    }
  ];

  const isActive = (href) => {
    if (href === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(href);
  };

  return (
    <aside className="fixed left-0 top-16 bottom-0 w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 sidebar-transition">
      <div className="flex flex-col h-full">
        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2 custom-scrollbar overflow-y-auto">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`
                  group flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-all duration-200
                  ${active
                    ? 'bg-blue-50 dark:bg-blue-900/50 text-blue-700 dark:text-blue-200 border-l-4 border-blue-500'
                    : 'text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-gray-900 dark:hover:text-white'
                  }
                `}
              >
                <Icon
                  className={`
                    mr-3 h-5 w-5 transition-colors duration-200
                    ${active
                      ? 'text-blue-500 dark:text-blue-400'
                      : 'text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300'
                    }
                  `}
                />
                <div className="flex-1 min-w-0">
                  <div className="font-medium">{item.name}</div>
                  <div className="text-xs text-gray-500 dark:text-gray-400 truncate">
                    {item.description}
                  </div>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Bottom Section */}
        <div className="px-4 py-4 border-t border-gray-200 dark:border-gray-700">
          {/* Quick Stats */}
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">Active Trades</span>
              <span className="font-semibold text-blue-600 dark:text-blue-400">3</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">Today's P&L</span>
              <span className="font-semibold text-green-600 dark:text-green-400">+$124.50</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500 dark:text-gray-400">Win Rate</span>
              <span className="font-semibold text-gray-900 dark:text-white">68%</span>
            </div>
          </div>

          {/* Version Info */}
          <div className="mt-4 pt-3 border-t border-gray-200 dark:border-gray-700">
            <div className="text-xs text-gray-400 dark:text-gray-500">
              Version 1.0.0
            </div>
            <div className="text-xs text-gray-400 dark:text-gray-500">
              Bitunix Trading Bot
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;