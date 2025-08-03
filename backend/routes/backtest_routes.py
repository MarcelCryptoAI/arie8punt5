from flask import Blueprint, request, jsonify
from models import BitunixBacktest, BitunixSettings, db
from services.telegram_parser import TelegramSignalParser
from services.backtest_engine import BacktestEngine
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

bp = Blueprint('backtest', __name__, url_prefix='/api/backtest')

@bp.route('/', methods=['GET'])
def get_backtests():
    """Get all backtests with pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        backtests = BitunixBacktest.query.order_by(
            BitunixBacktest.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'backtests': [backtest.to_dict() for backtest in backtests.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': backtests.total,
                'pages': backtests.pages,
                'has_next': backtests.has_next,
                'has_prev': backtests.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching backtests: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:backtest_id>', methods=['GET'])
def get_backtest(backtest_id):
    """Get a specific backtest by ID."""
    try:
        backtest = BitunixBacktest.query.get_or_404(backtest_id)
        backtest_dict = backtest.to_dict()
        
        # Include detailed results if available
        if backtest.trade_history:
            backtest_dict['trade_history'] = json.loads(backtest.trade_history)
        if backtest.equity_curve:
            backtest_dict['equity_curve'] = json.loads(backtest.equity_curve)
        
        return jsonify(backtest_dict)
        
    except Exception as e:
        logger.error(f"Error fetching backtest {backtest_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/create', methods=['POST'])
def create_backtest():
    """Create a new backtest."""
    try:
        data = request.get_json()
        
        name = data.get('name', f'Backtest {datetime.utcnow().strftime("%Y-%m-%d %H:%M")}')
        signals_text = data.get('signals', [])
        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')
        initial_balance = data.get('initial_balance', 1000.0)
        custom_settings = data.get('settings', {})
        
        if not signals_text:
            return jsonify({'error': 'Signals are required'}), 400
        
        # Parse dates
        start_date = None
        end_date = None
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
        
        # Parse signals
        parser = TelegramSignalParser()
        parsed_signals = []
        
        for signal_text in signals_text:
            parsed = parser.parse_signal(signal_text)
            if parsed.get('parsed_successfully', False):
                parsed_signals.append(parsed)
        
        if not parsed_signals:
            return jsonify({'error': 'No valid signals found'}), 400
        
        # Get current settings or use custom settings
        settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
        if settings:
            settings_dict = settings.to_dict()
        else:
            settings_dict = {}
        
        # Override with custom settings
        settings_dict.update(custom_settings)
        
        # Create backtest record
        backtest = BitunixBacktest(
            name=name,
            signals_data=json.dumps(parsed_signals),
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance,
            settings_snapshot=json.dumps(settings_dict),
            status='pending'
        )
        
        db.session.add(backtest)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'backtest': backtest.to_dict(),
            'parsed_signals': len(parsed_signals)
        })
        
    except Exception as e:
        logger.error(f"Error creating backtest: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:backtest_id>/run', methods=['POST'])
def run_backtest(backtest_id):
    """Run a backtest."""
    try:
        backtest = BitunixBacktest.query.get_or_404(backtest_id)
        
        if backtest.status == 'running':
            return jsonify({'error': 'Backtest is already running'}), 400
        
        if backtest.status == 'completed':
            return jsonify({'error': 'Backtest is already completed'}), 400
        
        # Update status to running
        backtest.status = 'running'
        db.session.commit()
        
        try:
            # Parse stored data
            signals_data = json.loads(backtest.signals_data)
            settings = json.loads(backtest.settings_snapshot)
            
            # Run backtest
            engine = BacktestEngine()
            results = engine.run_backtest(
                signals=signals_data,
                settings=settings,
                initial_balance=backtest.initial_balance,
                start_date=backtest.start_date,
                end_date=backtest.end_date
            )
            
            # Update backtest with results
            backtest.final_balance = results['final_balance']
            backtest.total_pnl = results['total_pnl']
            backtest.total_pnl_percentage = results['total_pnl_percentage']
            backtest.total_trades = results['total_trades']
            backtest.winning_trades = results['winning_trades']
            backtest.losing_trades = results['losing_trades']
            backtest.win_rate = results['win_rate']
            backtest.max_drawdown = results['max_drawdown']
            backtest.sharpe_ratio = results.get('sharpe_ratio')
            backtest.trade_history = json.dumps(results['trade_history'])
            backtest.equity_curve = json.dumps(results['equity_curve'])
            backtest.completed_at = datetime.utcnow()
            backtest.status = 'completed'
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'backtest': backtest.to_dict(),
                'results': results
            })
            
        except Exception as run_error:
            # Update status to failed
            backtest.status = 'failed'
            db.session.commit()
            raise run_error
        
    except Exception as e:
        logger.error(f"Error running backtest {backtest_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:backtest_id>', methods=['DELETE'])
def delete_backtest(backtest_id):
    """Delete a backtest."""
    try:
        backtest = BitunixBacktest.query.get_or_404(backtest_id)
        
        if backtest.status == 'running':
            return jsonify({'error': 'Cannot delete running backtest'}), 400
        
        db.session.delete(backtest)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Backtest {backtest_id} deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting backtest {backtest_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/compare', methods=['POST'])
def compare_backtests():
    """Compare multiple backtests."""
    try:
        data = request.get_json()
        backtest_ids = data.get('backtest_ids', [])
        
        if not backtest_ids or len(backtest_ids) < 2:
            return jsonify({'error': 'At least 2 backtest IDs required'}), 400
        
        backtests = BitunixBacktest.query.filter(
            BitunixBacktest.id.in_(backtest_ids),
            BitunixBacktest.status == 'completed'
        ).all()
        
        if len(backtests) != len(backtest_ids):
            return jsonify({'error': 'Some backtests not found or not completed'}), 400
        
        # Prepare comparison data
        comparison = {
            'backtests': [],
            'summary': {
                'best_pnl': None,
                'best_win_rate': None,
                'best_sharpe': None,
                'lowest_drawdown': None
            }
        }
        
        best_pnl = float('-inf')
        best_win_rate = 0
        best_sharpe = float('-inf')
        lowest_drawdown = float('inf')
        
        for backtest in backtests:
            bt_dict = backtest.to_dict()
            comparison['backtests'].append(bt_dict)
            
            # Track best metrics
            if backtest.total_pnl_percentage and backtest.total_pnl_percentage > best_pnl:
                best_pnl = backtest.total_pnl_percentage
                comparison['summary']['best_pnl'] = backtest.id
            
            if backtest.win_rate and backtest.win_rate > best_win_rate:
                best_win_rate = backtest.win_rate
                comparison['summary']['best_win_rate'] = backtest.id
            
            if backtest.sharpe_ratio and backtest.sharpe_ratio > best_sharpe:
                best_sharpe = backtest.sharpe_ratio
                comparison['summary']['best_sharpe'] = backtest.id
            
            if backtest.max_drawdown and backtest.max_drawdown < lowest_drawdown:
                lowest_drawdown = backtest.max_drawdown
                comparison['summary']['lowest_drawdown'] = backtest.id
        
        return jsonify({
            'success': True,
            'comparison': comparison
        })
        
    except Exception as e:
        logger.error(f"Error comparing backtests: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/template', methods=['GET'])
def get_template_signals():
    """Get template signals for backtesting."""
    template_signals = [
        "#BTC/USDT\nLONG\nEntry: 45000-46000\nLeverage: 5x\nTargets: 47000, 48000, 49000\nStop Loss: 44000",
        "#ETH/USDT\nSHORT\nEntry: 3200-3250\nLeverage: 3x\nTargets: 3100, 3000, 2900\nStop Loss: 3300",
        "#SOL/USDT\nLONG\nEntry: 180-185\nLeverage: 10x\nTargets: 190, 195, 200\nStop Loss: 175"
    ]
    
    return jsonify({
        'template_signals': template_signals,
        'description': 'Sample signals for backtesting'
    })

@bp.route('/stats', methods=['GET'])
def get_backtest_stats():
    """Get backtest statistics."""
    try:
        total_backtests = BitunixBacktest.query.count()
        completed_backtests = BitunixBacktest.query.filter_by(status='completed').count()
        running_backtests = BitunixBacktest.query.filter_by(status='running').count()
        failed_backtests = BitunixBacktest.query.filter_by(status='failed').count()
        
        # Best performing backtest
        best_backtest = BitunixBacktest.query.filter_by(status='completed').order_by(
            BitunixBacktest.total_pnl_percentage.desc()
        ).first()
        
        # Average performance metrics
        avg_metrics = db.session.query(
            db.func.avg(BitunixBacktest.total_pnl_percentage).label('avg_pnl'),
            db.func.avg(BitunixBacktest.win_rate).label('avg_win_rate'),
            db.func.avg(BitunixBacktest.max_drawdown).label('avg_drawdown')
        ).filter_by(status='completed').first()
        
        return jsonify({
            'total_backtests': total_backtests,
            'completed_backtests': completed_backtests,
            'running_backtests': running_backtests,
            'failed_backtests': failed_backtests,
            'best_backtest': best_backtest.to_dict() if best_backtest else None,
            'average_metrics': {
                'avg_pnl_percentage': float(avg_metrics.avg_pnl) if avg_metrics.avg_pnl else 0,
                'avg_win_rate': float(avg_metrics.avg_win_rate) if avg_metrics.avg_win_rate else 0,
                'avg_drawdown': float(avg_metrics.avg_drawdown) if avg_metrics.avg_drawdown else 0
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching backtest stats: {str(e)}")
        return jsonify({'error': str(e)}), 500