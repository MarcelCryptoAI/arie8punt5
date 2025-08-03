from flask import Blueprint, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from models import BitunixSignal, db
from services.telegram_parser import TelegramSignalParser
import json
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('signals', __name__, url_prefix='/api/signals')
parser = TelegramSignalParser()

@bp.route('/', methods=['GET'])
def get_signals():
    """Get all signals with pagination and filtering."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        coin = request.args.get('coin')
        position_type = request.args.get('position_type')
        processed = request.args.get('processed', type=bool)
        
        query = BitunixSignal.query
        
        # Apply filters
        if coin:
            query = query.filter(BitunixSignal.coin.ilike(f'%{coin}%'))
        if position_type:
            query = query.filter(BitunixSignal.position_type == position_type.upper())
        if processed is not None:
            query = query.filter(BitunixSignal.processed == processed)
        
        # Paginate
        signals = query.order_by(BitunixSignal.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'signals': [signal.to_dict() for signal in signals.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': signals.total,
                'pages': signals.pages,
                'has_next': signals.has_next,
                'has_prev': signals.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching signals: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:signal_id>', methods=['GET'])
def get_signal(signal_id):
    """Get a specific signal by ID."""
    try:
        signal = BitunixSignal.query.get_or_404(signal_id)
        return jsonify(signal.to_dict())
    except Exception as e:
        logger.error(f"Error fetching signal {signal_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/parse', methods=['POST'])
def parse_signal():
    """Parse a new signal from text."""
    try:
        data = request.get_json()
        signal_text = data.get('text', '')
        
        if not signal_text:
            return jsonify({'error': 'Signal text is required'}), 400
        
        # Parse the signal
        parsed_data = parser.parse_signal(signal_text)
        
        # Create new signal record
        signal = BitunixSignal(
            raw_text=signal_text,
            coin=parsed_data.get('coin'),
            pair=parsed_data.get('pair', 'USDT'),
            position_type=parsed_data.get('position_type'),
            entry_zones=json.dumps(parsed_data.get('entry_zones', [])),
            leverage=parsed_data.get('leverage', 1),
            cross_leverage=parsed_data.get('cross_leverage', False),
            targets=json.dumps(parsed_data.get('targets', [])),
            stop_loss=parsed_data.get('stop_loss'),
            parse_errors=json.dumps(parsed_data.get('parse_errors', [])),
            processed=False
        )
        
        db.session.add(signal)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'signal': signal.to_dict(),
            'parsed_data': parsed_data
        })
        
    except Exception as e:
        logger.error(f"Error parsing signal: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/batch-parse', methods=['POST'])
def batch_parse_signals():
    """Parse multiple signals in batch."""
    try:
        data = request.get_json()
        signal_texts = data.get('signals', [])
        
        if not signal_texts or not isinstance(signal_texts, list):
            return jsonify({'error': 'Array of signal texts is required'}), 400
        
        # Parse all signals
        parsed_results = parser.batch_parse_signals(signal_texts)
        
        # Create signal records
        signals_created = []
        for i, parsed_data in enumerate(parsed_results):
            signal = BitunixSignal(
                raw_text=signal_texts[i],
                coin=parsed_data.get('coin'),
                pair=parsed_data.get('pair', 'USDT'),
                position_type=parsed_data.get('position_type'),
                entry_zones=json.dumps(parsed_data.get('entry_zones', [])),
                leverage=parsed_data.get('leverage', 1),
                cross_leverage=parsed_data.get('cross_leverage', False),
                targets=json.dumps(parsed_data.get('targets', [])),
                stop_loss=parsed_data.get('stop_loss'),
                parse_errors=json.dumps(parsed_data.get('parse_errors', [])),
                processed=False
            )
            
            db.session.add(signal)
            signals_created.append(signal)
        
        db.session.commit()
        
        # Get parsing statistics
        stats = parser.get_parsing_stats(parsed_results)
        
        return jsonify({
            'success': True,
            'signals_created': len(signals_created),
            'signals': [signal.to_dict() for signal in signals_created],
            'parsing_stats': stats
        })
        
    except Exception as e:
        logger.error(f"Error batch parsing signals: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:signal_id>', methods=['PUT'])
def update_signal(signal_id):
    """Update an existing signal."""
    try:
        signal = BitunixSignal.query.get_or_404(signal_id)
        data = request.get_json()
        
        # Update allowed fields
        if 'coin' in data:
            signal.coin = data['coin']
        if 'position_type' in data:
            signal.position_type = data['position_type']
        if 'entry_zones' in data:
            signal.entry_zones = json.dumps(data['entry_zones'])
        if 'leverage' in data:
            signal.leverage = data['leverage']
        if 'cross_leverage' in data:
            signal.cross_leverage = data['cross_leverage']
        if 'targets' in data:
            signal.targets = json.dumps(data['targets'])
        if 'stop_loss' in data:
            signal.stop_loss = data['stop_loss']
        if 'processed' in data:
            signal.processed = data['processed']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'signal': signal.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating signal {signal_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:signal_id>', methods=['DELETE'])
def delete_signal(signal_id):
    """Delete a signal."""
    try:
        signal = BitunixSignal.query.get_or_404(signal_id)
        
        # Check if signal has associated trades
        if signal.trades:
            return jsonify({
                'error': 'Cannot delete signal with associated trades'
            }), 400
        
        db.session.delete(signal)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Signal {signal_id} deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting signal {signal_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/stats', methods=['GET'])
def get_signal_stats():
    """Get signal statistics."""
    try:
        total_signals = BitunixSignal.query.count()
        processed_signals = BitunixSignal.query.filter_by(processed=True).count()
        unprocessed_signals = total_signals - processed_signals
        
        # Count by position type
        long_signals = BitunixSignal.query.filter_by(position_type='LONG').count()
        short_signals = BitunixSignal.query.filter_by(position_type='SHORT').count()
        
        # Count by coin (top 10)
        coin_stats = db.session.query(
            BitunixSignal.coin, 
            db.func.count(BitunixSignal.id).label('count')
        ).group_by(BitunixSignal.coin).order_by(
            db.func.count(BitunixSignal.id).desc()
        ).limit(10).all()
        
        return jsonify({
            'total_signals': total_signals,
            'processed_signals': processed_signals,
            'unprocessed_signals': unprocessed_signals,
            'long_signals': long_signals,
            'short_signals': short_signals,
            'top_coins': [{'coin': coin, 'count': count} for coin, count in coin_stats]
        })
        
    except Exception as e:
        logger.error(f"Error fetching signal stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/reparse/<int:signal_id>', methods=['POST'])
def reparse_signal(signal_id):
    """Reparse an existing signal."""
    try:
        signal = BitunixSignal.query.get_or_404(signal_id)
        
        # Parse the signal again
        parsed_data = parser.parse_signal(signal.raw_text)
        
        # Update the signal with new parsed data
        signal.coin = parsed_data.get('coin')
        signal.pair = parsed_data.get('pair', 'USDT')
        signal.position_type = parsed_data.get('position_type')
        signal.entry_zones = json.dumps(parsed_data.get('entry_zones', []))
        signal.leverage = parsed_data.get('leverage', 1)
        signal.cross_leverage = parsed_data.get('cross_leverage', False)
        signal.targets = json.dumps(parsed_data.get('targets', []))
        signal.stop_loss = parsed_data.get('stop_loss')
        signal.parse_errors = json.dumps(parsed_data.get('parse_errors', []))
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'signal': signal.to_dict(),
            'parsed_data': parsed_data
        })
        
    except Exception as e:
        logger.error(f"Error reparsing signal {signal_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500