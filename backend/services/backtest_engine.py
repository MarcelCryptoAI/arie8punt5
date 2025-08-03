import requests
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class BacktestEngine:
    """
    Backtesting engine for Telegram trading signals.
    Simulates trading with historical data and calculates performance metrics.
    """
    
    def __init__(self):
        self.base_url = "https://api.binance.com"  # Using Binance for historical data
        
    def run_backtest(self, signals: List[Dict], settings: Dict, 
                    initial_balance: float = 1000.0,
                    start_date: datetime = None, 
                    end_date: datetime = None) -> Dict:
        """
        Run a complete backtest on the given signals.
        
        Args:
            signals: List of parsed signal dictionaries
            settings: Trading settings and configuration
            initial_balance: Starting balance in USDT
            start_date: Start date for backtest
            end_date: End date for backtest
            
        Returns:
            Dict: Complete backtest results with metrics
        """
        try:
            # Default date range if not provided
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            # Initialize backtest state
            balance = initial_balance
            positions = {}
            trade_history = []
            equity_curve = []
            
            logger.info(f"Starting backtest with {len(signals)} signals from {start_date} to {end_date}")
            
            # Process each signal
            for signal in signals:
                try:
                    if not signal.get('coin') or not signal.get('entry_zones'):
                        continue
                    
                    # Simulate trade execution
                    trade_result = self._simulate_trade(
                        signal, settings, balance, start_date, end_date
                    )
                    
                    if trade_result:
                        trade_history.append(trade_result)
                        balance += trade_result['pnl']
                        
                        # Record equity point
                        equity_curve.append({
                            'timestamp': trade_result['exit_time'],
                            'balance': balance,
                            'trade_pnl': trade_result['pnl']
                        })
                        
                        logger.info(f"Trade completed: {signal['coin']} {signal['position_type']} PnL: {trade_result['pnl']:.2f}")
                
                except Exception as e:
                    logger.error(f"Error processing signal {signal}: {str(e)}")
                    continue
            
            # Calculate performance metrics
            metrics = self._calculate_metrics(
                trade_history, initial_balance, balance, equity_curve
            )
            
            return {
                'initial_balance': initial_balance,
                'final_balance': balance,
                'total_pnl': balance - initial_balance,
                'total_pnl_percentage': ((balance - initial_balance) / initial_balance) * 100,
                'total_trades': len(trade_history),
                'winning_trades': sum(1 for t in trade_history if t['pnl'] > 0),
                'losing_trades': sum(1 for t in trade_history if t['pnl'] <= 0),
                'win_rate': (sum(1 for t in trade_history if t['pnl'] > 0) / len(trade_history) * 100) if trade_history else 0,
                'max_drawdown': metrics['max_drawdown'],
                'sharpe_ratio': metrics['sharpe_ratio'],
                'trade_history': trade_history,
                'equity_curve': equity_curve,
                'metrics': metrics
            }
            
        except Exception as e:
            logger.error(f"Backtest error: {str(e)}")
            raise
    
    def _simulate_trade(self, signal: Dict, settings: Dict, balance: float,
                       start_date: datetime, end_date: datetime) -> Optional[Dict]:
        """Simulate a single trade based on signal and historical data."""
        try:
            coin = signal['coin']
            pair = signal.get('pair', 'USDT')
            symbol = f"{coin}{pair}"
            position_type = signal['position_type']
            entry_zones = signal.get('entry_zones', [])
            targets = signal.get('targets', [])
            stop_loss = signal.get('stop_loss')
            
            if not entry_zones:
                return None
            
            # Get historical data
            historical_data = self._get_historical_data(symbol, start_date, end_date)
            if not historical_data:
                return None
            
            # Calculate position size
            position_size = self._calculate_position_size(
                balance, settings.get('default_position_size', 10.0),
                settings.get('risk_percentage', 2.0),
                entry_zones[0], stop_loss
            )
            
            # Find entry point
            entry_price, entry_time = self._find_entry_point(
                historical_data, entry_zones, position_type
            )
            
            if not entry_price:
                return None
            
            # Find exit point (target or stop loss)
            exit_price, exit_time, exit_reason = self._find_exit_point(
                historical_data, entry_time, targets, stop_loss, position_type
            )
            
            if not exit_price:
                return None
            
            # Calculate PnL
            if position_type == 'LONG':
                pnl = (exit_price - entry_price) / entry_price * position_size
            else:  # SHORT
                pnl = (entry_price - exit_price) / entry_price * position_size
            
            # Apply leverage
            leverage = signal.get('leverage', 1)
            pnl *= leverage
            
            return {
                'coin': coin,
                'symbol': symbol,
                'position_type': position_type,
                'entry_price': entry_price,
                'exit_price': exit_price,
                'entry_time': entry_time.isoformat(),
                'exit_time': exit_time.isoformat(),
                'position_size': position_size,
                'leverage': leverage,
                'pnl': pnl,
                'pnl_percentage': (pnl / position_size) * 100,
                'exit_reason': exit_reason,
                'duration_hours': (exit_time - entry_time).total_seconds() / 3600
            }
            
        except Exception as e:
            logger.error(f"Error simulating trade for {signal}: {str(e)}")
            return None
    
    def _get_historical_data(self, symbol: str, start_date: datetime, 
                           end_date: datetime) -> Optional[pd.DataFrame]:
        """Get historical price data from Binance API."""
        try:
            # Convert to Binance symbol format
            if symbol.endswith('USDT'):
                binance_symbol = symbol
            else:
                binance_symbol = f"{symbol}USDT"
            
            # Convert dates to milliseconds
            start_ms = int(start_date.timestamp() * 1000)
            end_ms = int(end_date.timestamp() * 1000)
            
            # Get kline data (1 hour intervals)
            url = f"{self.base_url}/api/v3/klines"
            params = {
                'symbol': binance_symbol,
                'interval': '1h',
                'startTime': start_ms,
                'endTime': end_ms,
                'limit': 1000
            }
            
            response = requests.get(url, params=params)
            if response.status_code != 200:
                logger.warning(f"Failed to get data for {symbol}: {response.status_code}")
                return None
            
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert data types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Got {len(df)} data points for {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"Error getting historical data for {symbol}: {str(e)}")
            return None
    
    def _find_entry_point(self, data: pd.DataFrame, entry_zones: List[float],
                         position_type: str) -> tuple:
        """Find the first valid entry point in historical data."""
        for idx, row in data.iterrows():
            price_range = [row['low'], row['high']]
            
            for entry_price in entry_zones:
                # Check if entry price was hit during this candle
                if price_range[0] <= entry_price <= price_range[1]:
                    return entry_price, idx
        
        return None, None
    
    def _find_exit_point(self, data: pd.DataFrame, entry_time: datetime,
                        targets: List[float], stop_loss: float,
                        position_type: str) -> tuple:
        """Find exit point (target or stop loss) after entry."""
        # Filter data after entry time
        exit_data = data[data.index > entry_time]
        
        if exit_data.empty:
            return None, None, None
        
        for idx, row in exit_data.iterrows():
            price_range = [row['low'], row['high']]
            
            # Check stop loss first
            if stop_loss:
                if position_type == 'LONG' and price_range[0] <= stop_loss:
                    return stop_loss, idx, 'stop_loss'
                elif position_type == 'SHORT' and price_range[1] >= stop_loss:
                    return stop_loss, idx, 'stop_loss'
            
            # Check targets
            for target in targets:
                if position_type == 'LONG' and price_range[1] >= target:
                    return target, idx, 'target'
                elif position_type == 'SHORT' and price_range[0] <= target:
                    return target, idx, 'target'
        
        # If no exit found, use last available price
        last_row = exit_data.iloc[-1]
        return last_row['close'], exit_data.index[-1], 'timeout'
    
    def _calculate_position_size(self, balance: float, default_size: float,
                               risk_percentage: float, entry_price: float,
                               stop_loss: float) -> float:
        """Calculate position size based on risk management."""
        if not stop_loss or not entry_price or stop_loss <= 0 or entry_price <= 0:
            return min(default_size, balance * 0.1)  # Max 10% of balance
        
        # Risk-based position sizing
        risk_per_unit = abs(entry_price - stop_loss) / entry_price
        if risk_per_unit > 0:
            risk_amount = balance * (risk_percentage / 100)
            max_size = risk_amount / risk_per_unit
            return min(max_size, balance * 0.2)  # Max 20% of balance
        
        return min(default_size, balance * 0.1)
    
    def _calculate_metrics(self, trade_history: List[Dict], initial_balance: float,
                          final_balance: float, equity_curve: List[Dict]) -> Dict:
        """Calculate advanced performance metrics."""
        try:
            if not trade_history:
                return {
                    'max_drawdown': 0,
                    'sharpe_ratio': 0,
                    'average_trade': 0,
                    'profit_factor': 0
                }
            
            # Convert equity curve to series for calculations
            equity_values = [initial_balance] + [point['balance'] for point in equity_curve]
            
            # Calculate maximum drawdown
            peak = equity_values[0]
            max_drawdown = 0
            
            for value in equity_values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak * 100
                max_drawdown = max(max_drawdown, drawdown)
            
            # Calculate returns for Sharpe ratio
            returns = []
            for i in range(1, len(equity_values)):
                ret = (equity_values[i] - equity_values[i-1]) / equity_values[i-1]
                returns.append(ret)
            
            # Sharpe ratio (simplified, assuming daily returns)
            if returns and np.std(returns) > 0:
                avg_return = np.mean(returns)
                sharpe_ratio = avg_return / np.std(returns) * np.sqrt(252)  # Annualized
            else:
                sharpe_ratio = 0
            
            # Other metrics
            trade_pnls = [trade['pnl'] for trade in trade_history]
            winning_trades = [pnl for pnl in trade_pnls if pnl > 0]
            losing_trades = [pnl for pnl in trade_pnls if pnl <= 0]
            
            average_trade = np.mean(trade_pnls) if trade_pnls else 0
            
            # Profit factor
            gross_profit = sum(winning_trades) if winning_trades else 0
            gross_loss = abs(sum(losing_trades)) if losing_trades else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
            
            return {
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'average_trade': average_trade,
                'profit_factor': profit_factor,
                'gross_profit': gross_profit,
                'gross_loss': gross_loss,
                'largest_win': max(winning_trades) if winning_trades else 0,
                'largest_loss': min(losing_trades) if losing_trades else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating metrics: {str(e)}")
            return {
                'max_drawdown': 0,
                'sharpe_ratio': 0,
                'average_trade': 0,
                'profit_factor': 0
            }