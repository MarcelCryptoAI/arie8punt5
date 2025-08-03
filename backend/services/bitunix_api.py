import hashlib
import hmac
import time
import json
import requests
from typing import Dict, List, Optional, Tuple
import logging
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

class BitunixAPI:
    """
    Bitunix exchange API integration for futures trading.
    Handles authentication, order management, and position monitoring.
    """
    
    def __init__(self, api_key: str, api_secret: str, api_passphrase: str, testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.api_passphrase = api_passphrase
        self.testnet = testnet
        
        # Base URLs
        if testnet:
            self.base_url = "https://sandbox-api.bitunix.com"
        else:
            self.base_url = "https://api.bitunix.com"
        
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'BX-ACCESS-KEY': self.api_key,
        })
    
    def _generate_signature(self, timestamp: str, method: str, request_path: str, body: str = '') -> str:
        """Generate HMAC SHA256 signature for API authentication."""
        message = timestamp + method + request_path + body
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """Make authenticated API request to Bitunix."""
        try:
            timestamp = str(int(time.time() * 1000))
            request_path = endpoint
            
            # Prepare body
            body = ''
            if data:
                body = json.dumps(data, separators=(',', ':'))
            
            # Add query parameters to path if GET request
            if method == 'GET' and params:
                query_string = urlencode(params)
                request_path += '?' + query_string
            
            # Generate signature
            signature = self._generate_signature(timestamp, method, request_path, body)
            
            # Set headers
            headers = {
                'BX-ACCESS-KEY': self.api_key,
                'BX-ACCESS-SIGN': signature,
                'BX-ACCESS-TIMESTAMP': timestamp,
                'BX-ACCESS-PASSPHRASE': self.api_passphrase,
                'Content-Type': 'application/json'
            }
            
            # Make request
            url = self.base_url + endpoint
            
            if method == 'GET':
                response = self.session.get(url, params=params, headers=headers)
            elif method == 'POST':
                response = self.session.post(url, data=body, headers=headers)
            elif method == 'DELETE':
                response = self.session.delete(url, data=body, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Handle response
            if response.status_code == 200:
                return response.json()
            else:
                error_msg = f"API request failed: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"API request error: {str(e)}")
            raise
    
    def get_account_info(self) -> Dict:
        """Get account information and balances."""
        return self._make_request('GET', '/api/v1/account')
    
    def get_balance(self) -> Dict:
        """Get account balance."""
        return self._make_request('GET', '/api/v1/account/balance')
    
    def get_positions(self, symbol: str = None) -> List[Dict]:
        """Get current positions."""
        endpoint = '/api/v1/position'
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        response = self._make_request('GET', endpoint, params=params)
        return response.get('data', [])
    
    def get_ticker(self, symbol: str) -> Dict:
        """Get ticker information for a symbol."""
        params = {'symbol': symbol}
        return self._make_request('GET', '/api/v1/ticker', params=params)
    
    def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """Get orderbook depth."""
        params = {'symbol': symbol, 'limit': limit}
        return self._make_request('GET', '/api/v1/depth', params=params)
    
    def place_order(self, symbol: str, side: str, order_type: str, size: float, 
                   price: float = None, leverage: int = None, 
                   reduce_only: bool = False, time_in_force: str = 'GTC') -> Dict:
        """
        Place a new order.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'buy' or 'sell'
            order_type: 'limit', 'market'
            size: Order size
            price: Order price (required for limit orders)
            leverage: Leverage (optional)
            reduce_only: Whether this is a reduce-only order
            time_in_force: Time in force ('GTC', 'IOC', 'FOK')
        """
        data = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'size': str(size),
            'timeInForce': time_in_force,
            'reduceOnly': reduce_only
        }
        
        if price and order_type == 'limit':
            data['price'] = str(price)
        
        if leverage:
            data['leverage'] = str(leverage)
        
        return self._make_request('POST', '/api/v1/order', data=data)
    
    def cancel_order(self, order_id: str, symbol: str) -> Dict:
        """Cancel an existing order."""
        data = {
            'orderId': order_id,
            'symbol': symbol
        }
        return self._make_request('DELETE', '/api/v1/order', data=data)
    
    def get_order(self, order_id: str, symbol: str) -> Dict:
        """Get order details."""
        params = {
            'orderId': order_id,
            'symbol': symbol
        }
        return self._make_request('GET', '/api/v1/order', params=params)
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Get all open orders."""
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        response = self._make_request('GET', '/api/v1/orders', params=params)
        return response.get('data', [])
    
    def get_order_history(self, symbol: str = None, limit: int = 100) -> List[Dict]:
        """Get order history."""
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        
        response = self._make_request('GET', '/api/v1/orders/history', params=params)
        return response.get('data', [])
    
    def set_leverage(self, symbol: str, leverage: int, margin_mode: str = 'isolated') -> Dict:
        """Set leverage for a symbol."""
        data = {
            'symbol': symbol,
            'leverage': str(leverage),
            'marginMode': margin_mode  # 'isolated' or 'cross'
        }
        return self._make_request('POST', '/api/v1/position/leverage', data=data)
    
    def get_funding_rate(self, symbol: str) -> Dict:
        """Get funding rate for a symbol."""
        params = {'symbol': symbol}
        return self._make_request('GET', '/api/v1/funding/rate', params=params)
    
    def get_klines(self, symbol: str, interval: str, limit: int = 500, 
                   start_time: int = None, end_time: int = None) -> List[List]:
        """
        Get candlestick data.
        
        Args:
            symbol: Trading pair
            interval: Kline interval ('1m', '5m', '15m', '30m', '1h', '4h', '1d')
            limit: Number of records to return (max 1000)
            start_time: Start time in milliseconds
            end_time: End time in milliseconds
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        response = self._make_request('GET', '/api/v1/klines', params=params)
        return response.get('data', [])

class BitunixTradeManager:
    """
    High-level trade management for Bitunix signals.
    Handles DCA entries, targets, and stop losses.
    """
    
    def __init__(self, api: BitunixAPI):
        self.api = api
    
    def execute_signal(self, signal_data: Dict, settings: Dict) -> Dict:
        """
        Execute a parsed signal with the given settings.
        
        Args:
            signal_data: Parsed signal from TelegramSignalParser
            settings: Trading settings and configuration
            
        Returns:
            Dict: Execution results with order IDs and status
        """
        try:
            symbol = f"{signal_data['coin']}{signal_data['pair']}"
            position_type = signal_data['position_type']
            entry_zones = signal_data['entry_zones']
            targets = signal_data['targets']
            stop_loss = signal_data['stop_loss']
            leverage = signal_data.get('leverage', settings.get('default_leverage', 1))
            
            # Set leverage
            margin_mode = 'cross' if signal_data.get('cross_leverage', False) else 'isolated'
            self.api.set_leverage(symbol, leverage, margin_mode)
            
            # Calculate position size
            position_size = self._calculate_position_size(
                settings.get('default_position_size', 10.0),
                settings.get('risk_percentage', 2.0),
                entry_zones[0] if entry_zones else 0,
                stop_loss
            )
            
            # Place entry orders (DCA)
            entry_orders = self._place_entry_orders(
                symbol, position_type, entry_zones, position_size, settings
            )
            
            # Place target orders
            target_orders = self._place_target_orders(
                symbol, position_type, targets, position_size, settings
            )
            
            # Place stop loss order
            stop_order = self._place_stop_loss_order(
                symbol, position_type, stop_loss, position_size
            )
            
            return {
                'success': True,
                'symbol': symbol,
                'position_type': position_type,
                'position_size': position_size,
                'leverage': leverage,
                'entry_orders': entry_orders,
                'target_orders': target_orders,
                'stop_order': stop_order,
                'message': f"Signal executed for {symbol} {position_type}"
            }
            
        except Exception as e:
            logger.error(f"Error executing signal: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f"Failed to execute signal: {str(e)}"
            }
    
    def _calculate_position_size(self, base_size: float, risk_percentage: float,
                               entry_price: float, stop_loss: float) -> float:
        """Calculate position size based on risk management."""
        if not stop_loss or not entry_price or stop_loss <= 0 or entry_price <= 0:
            return base_size
        
        # Simple risk-based sizing
        risk_per_unit = abs(entry_price - stop_loss) / entry_price
        if risk_per_unit > 0:
            max_size = (risk_percentage / 100) / risk_per_unit * base_size
            return min(max_size, base_size * 5)  # Cap at 5x base size
        
        return base_size
    
    def _place_entry_orders(self, symbol: str, position_type: str, 
                          entry_zones: List[float], total_size: float, 
                          settings: Dict) -> List[Dict]:
        """Place DCA entry orders."""
        if not entry_zones:
            return []
        
        side = 'buy' if position_type == 'LONG' else 'sell'
        entry_distribution = settings.get('entry_distribution', [40, 35, 25])
        entry_steps = min(len(entry_zones), len(entry_distribution))
        
        orders = []
        for i in range(entry_steps):
            entry_price = entry_zones[i]
            size_percentage = entry_distribution[i] / 100
            order_size = total_size * size_percentage
            
            try:
                order = self.api.place_order(
                    symbol=symbol,
                    side=side,
                    order_type='limit',
                    size=order_size,
                    price=entry_price
                )
                orders.append(order)
                logger.info(f"Entry order placed: {symbol} {side} {order_size} @ {entry_price}")
            except Exception as e:
                logger.error(f"Failed to place entry order: {str(e)}")
        
        return orders
    
    def _place_target_orders(self, symbol: str, position_type: str,
                           targets: List[float], total_size: float,
                           settings: Dict) -> List[Dict]:
        """Place target/take profit orders."""
        if not targets:
            return []
        
        side = 'sell' if position_type == 'LONG' else 'buy'
        target_distribution = settings.get('target_distribution', [50, 30, 20])
        target_steps = min(len(targets), len(target_distribution))
        
        orders = []
        for i in range(target_steps):
            target_price = targets[i]
            size_percentage = target_distribution[i] / 100
            order_size = total_size * size_percentage
            
            try:
                order = self.api.place_order(
                    symbol=symbol,
                    side=side,
                    order_type='limit',
                    size=order_size,
                    price=target_price,
                    reduce_only=True
                )
                orders.append(order)
                logger.info(f"Target order placed: {symbol} {side} {order_size} @ {target_price}")
            except Exception as e:
                logger.error(f"Failed to place target order: {str(e)}")
        
        return orders
    
    def _place_stop_loss_order(self, symbol: str, position_type: str,
                             stop_loss: float, total_size: float) -> Optional[Dict]:
        """Place stop loss order."""
        if not stop_loss:
            return None
        
        side = 'sell' if position_type == 'LONG' else 'buy'
        
        try:
            order = self.api.place_order(
                symbol=symbol,
                side=side,
                order_type='stop_market',
                size=total_size,
                price=stop_loss,
                reduce_only=True
            )
            logger.info(f"Stop loss order placed: {symbol} {side} {total_size} @ {stop_loss}")
            return order
        except Exception as e:
            logger.error(f"Failed to place stop loss order: {str(e)}")
            return None
    
    def monitor_position(self, symbol: str) -> Dict:
        """Monitor position status and PnL."""
        try:
            positions = self.api.get_positions(symbol)
            if positions:
                position = positions[0]
                return {
                    'symbol': position.get('symbol'),
                    'side': position.get('side'),
                    'size': float(position.get('size', 0)),
                    'entry_price': float(position.get('avgPrice', 0)),
                    'mark_price': float(position.get('markPrice', 0)),
                    'pnl': float(position.get('unrealizedPnl', 0)),
                    'pnl_percentage': float(position.get('unrealizedPnlPcnt', 0)) * 100,
                    'margin': float(position.get('positionMargin', 0)),
                    'leverage': int(position.get('leverage', 1))
                }
            else:
                return {'symbol': symbol, 'status': 'no_position'}
        except Exception as e:
            logger.error(f"Error monitoring position: {str(e)}")
            return {'error': str(e)}