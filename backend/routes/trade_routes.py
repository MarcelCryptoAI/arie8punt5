from flask import Blueprint, request, jsonify
from models import BitunixTrade, BitunixSignal, BitunixSettings, db
from services.bitunix_api import BitunixAPI, BitunixTradeManager
import json
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('trades', __name__, url_prefix='/api/trades')

def get_api_instance():
    """Get authenticated Bitunix API instance."""
    settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
    if not settings or not settings.api_key:
        raise Exception("Bitunix API not configured")
    
    return BitunixAPI(
        api_key=settings.api_key,
        api_secret=settings.api_secret,
        api_passphrase=settings.api_passphrase,
        testnet=settings.testnet
    )

@bp.route('/', methods=['GET'])
def get_trades():
    """Get all trades with pagination and filtering."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        coin = request.args.get('coin')
        status = request.args.get('status')
        position_type = request.args.get('position_type')
        
        query = BitunixTrade.query
        
        # Apply filters
        if coin:
            query = query.filter(BitunixTrade.coin.ilike(f'%{coin}%'))
        if status:
            query = query.filter(BitunixTrade.status == status)
        if position_type:
            query = query.filter(BitunixTrade.position_type == position_type.upper())
        
        # Paginate
        trades = query.order_by(BitunixTrade.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'trades': [trade.to_dict() for trade in trades.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': trades.total,
                'pages': trades.pages,
                'has_next': trades.has_next,
                'has_prev': trades.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching trades: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:trade_id>', methods=['GET'])
def get_trade(trade_id):
    """Get a specific trade by ID."""
    try:
        trade = BitunixTrade.query.get_or_404(trade_id)
        return jsonify(trade.to_dict())
    except Exception as e:
        logger.error(f"Error fetching trade {trade_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/execute/<int:signal_id>', methods=['POST'])
def execute_signal(signal_id):
    """Execute a signal as a trade."""
    try:
        signal = BitunixSignal.query.get_or_404(signal_id)
        settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
        
        if not settings:
            return jsonify({'error': 'Trading settings not configured'}), 400
        
        # Check if signal already has trades
        existing_trade = BitunixTrade.query.filter_by(signal_id=signal_id).first()
        if existing_trade:
            return jsonify({'error': 'Signal already executed'}), 400
        
        # Get API instance and trade manager
        api = get_api_instance()
        trade_manager = BitunixTradeManager(api)
        
        # Execute the signal
        execution_result = trade_manager.execute_signal(
            signal.to_dict(), 
            settings.to_dict()
        )
        
        if execution_result['success']:
            # Create trade record
            trade = BitunixTrade(
                signal_id=signal_id,
                coin=signal.coin,
                pair=signal.pair,
                position_type=signal.position_type,
                size=execution_result['position_size'],
                leverage=execution_result['leverage'],
                entry_orders=json.dumps([order.get('orderId') for order in execution_result.get('entry_orders', [])]),
                target_orders=json.dumps([order.get('orderId') for order in execution_result.get('target_orders', [])]),
                stop_loss_order_id=execution_result.get('stop_order', {}).get('orderId'),
                status='active'
            )
            
            # Mark signal as processed
            signal.processed = True
            
            db.session.add(trade)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'trade': trade.to_dict(),
                'execution_result': execution_result
            })
        else:
            return jsonify({
                'success': False,
                'error': execution_result.get('error', 'Unknown error')
            }), 400
            
    except Exception as e:
        logger.error(f"Error executing signal {signal_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:trade_id>/update', methods=['POST'])
def update_trade_status(trade_id):
    """Update trade status by checking exchange."""
    try:
        trade = BitunixTrade.query.get_or_404(trade_id)
        api = get_api_instance()
        trade_manager = BitunixTradeManager(api)
        
        # Monitor position
        symbol = f"{trade.coin}{trade.pair}"
        position_data = trade_manager.monitor_position(symbol)
        
        if 'error' not in position_data:
            # Update trade with position data
            if 'pnl' in position_data:
                trade.pnl = position_data['pnl']
            if 'pnl_percentage' in position_data:
                trade.pnl_percentage = position_data['pnl_percentage']
            if 'entry_price' in position_data:
                trade.entry_price = position_data['entry_price']
            
            # Check if position is closed
            if position_data.get('status') == 'no_position':
                trade.status = 'closed'
                trade.closed_at = db.func.now()
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'trade': trade.to_dict(),
                'position_data': position_data
            })
        else:
            return jsonify({
                'success': False,
                'error': position_data['error']
            }), 400
            
    except Exception as e:
        logger.error(f"Error updating trade {trade_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:trade_id>/close', methods=['POST'])
def close_trade(trade_id):
    """Manually close a trade."""
    try:
        trade = BitunixTrade.query.get_or_404(trade_id)
        
        if trade.status in ['closed', 'cancelled']:
            return jsonify({'error': 'Trade is already closed'}), 400
        
        api = get_api_instance()
        symbol = f"{trade.coin}{trade.pair}"
        
        # Get current position
        positions = api.get_positions(symbol)
        if not positions:
            return jsonify({'error': 'No active position found'}), 400
        
        position = positions[0]
        position_size = float(position.get('size', 0))
        
        if position_size == 0:
            trade.status = 'closed'
            trade.closed_at = db.func.now()
            db.session.commit()
            return jsonify({'success': True, 'message': 'Position already closed'})
        
        # Place market order to close position
        side = 'sell' if trade.position_type == 'LONG' else 'buy'
        close_order = api.place_order(
            symbol=symbol,
            side=side,
            order_type='market',
            size=position_size,
            reduce_only=True
        )
        
        # Update trade status
        trade.status = 'closed'
        trade.closed_at = db.func.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'trade': trade.to_dict(),
            'close_order': close_order
        })
        
    except Exception as e:
        logger.error(f"Error closing trade {trade_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/stats', methods=['GET'])
def get_trade_stats():
    """Get trading statistics."""
    try:
        total_trades = BitunixTrade.query.count()
        active_trades = BitunixTrade.query.filter_by(status='active').count()
        closed_trades = BitunixTrade.query.filter_by(status='closed').count()
        
        # PnL statistics
        closed_trades_query = BitunixTrade.query.filter_by(status='closed')
        total_pnl = db.session.query(db.func.sum(BitunixTrade.pnl)).filter_by(status='closed').scalar() or 0
        winning_trades = closed_trades_query.filter(BitunixTrade.pnl > 0).count()
        losing_trades = closed_trades_query.filter(BitunixTrade.pnl < 0).count()
        
        win_rate = (winning_trades / closed_trades * 100) if closed_trades > 0 else 0
        
        # Top performing coins
        coin_performance = db.session.query(
            BitunixTrade.coin,
            db.func.sum(BitunixTrade.pnl).label('total_pnl'),
            db.func.count(BitunixTrade.id).label('trade_count')
        ).filter_by(status='closed').group_by(BitunixTrade.coin).order_by(
            db.func.sum(BitunixTrade.pnl).desc()
        ).limit(10).all()
        
        return jsonify({
            'total_trades': total_trades,
            'active_trades': active_trades,
            'closed_trades': closed_trades,
            'total_pnl': total_pnl,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': round(win_rate, 2),
            'top_coins': [
                {
                    'coin': coin,
                    'total_pnl': float(total_pnl),
                    'trade_count': trade_count
                }
                for coin, total_pnl, trade_count in coin_performance
            ]
        })
        
    except Exception as e:
        logger.error(f"Error fetching trade stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/active', methods=['GET'])
def get_active_trades():
    """Get all active trades with current status."""
    try:
        active_trades = BitunixTrade.query.filter_by(status='active').all()
        
        if not active_trades:
            return jsonify({'trades': []})
        
        # Get API instance for position monitoring
        try:
            api = get_api_instance()
            trade_manager = BitunixTradeManager(api)
            
            trades_with_status = []
            for trade in active_trades:
                symbol = f"{trade.coin}{trade.pair}"
                position_data = trade_manager.monitor_position(symbol)
                
                trade_dict = trade.to_dict()
                trade_dict['position_data'] = position_data
                trades_with_status.append(trade_dict)
            
            return jsonify({'trades': trades_with_status})
            
        except Exception as api_error:
            # Return trades without live data if API fails
            logger.warning(f"API error, returning trades without live data: {str(api_error)}")
            return jsonify({
                'trades': [trade.to_dict() for trade in active_trades],
                'warning': 'Live position data unavailable'
            })
        
    except Exception as e:
        logger.error(f"Error fetching active trades: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/history', methods=['GET'])
def get_trade_history():
    """Get trade history with performance metrics."""
    try:
        days = request.args.get('days', 30, type=int)
        
        # Get trades from last N days
        from datetime import datetime, timedelta
        start_date = datetime.utcnow() - timedelta(days=days)
        
        trades = BitunixTrade.query.filter(
            BitunixTrade.created_at >= start_date,
            BitunixTrade.status == 'closed'
        ).order_by(BitunixTrade.closed_at.desc()).all()
        
        # Calculate performance metrics
        total_trades = len(trades)
        total_pnl = sum(trade.pnl for trade in trades if trade.pnl)
        winning_trades = sum(1 for trade in trades if trade.pnl and trade.pnl > 0)
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        # Daily performance
        daily_pnl = {}
        for trade in trades:
            if trade.closed_at and trade.pnl:
                date_key = trade.closed_at.date().isoformat()
                daily_pnl[date_key] = daily_pnl.get(date_key, 0) + trade.pnl
        
        return jsonify({
            'trades': [trade.to_dict() for trade in trades],
            'performance': {
                'total_trades': total_trades,
                'total_pnl': total_pnl,
                'winning_trades': winning_trades,
                'losing_trades': total_trades - winning_trades,
                'win_rate': round(win_rate, 2),
                'daily_pnl': daily_pnl
            },
            'period_days': days
        })
        
    except Exception as e:
        logger.error(f"Error fetching trade history: {str(e)}")
        return jsonify({'error': str(e)}), 500