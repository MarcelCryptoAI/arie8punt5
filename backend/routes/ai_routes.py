from flask import Blueprint, request, jsonify
from models import BitunixAIOptimization, BitunixBacktest, BitunixSettings, db
from services.ai_optimizer import AIOptimizer
import json
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('ai', __name__, url_prefix='/api/ai')

@bp.route('/optimizations', methods=['GET'])
def get_optimizations():
    """Get all AI optimizations with pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        optimizations = BitunixAIOptimization.query.order_by(
            BitunixAIOptimization.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'optimizations': [opt.to_dict() for opt in optimizations.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': optimizations.total,
                'pages': optimizations.pages,
                'has_next': optimizations.has_next,
                'has_prev': optimizations.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching AI optimizations: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/optimizations/<int:optimization_id>', methods=['GET'])
def get_optimization(optimization_id):
    """Get a specific AI optimization by ID."""
    try:
        optimization = BitunixAIOptimization.query.get_or_404(optimization_id)
        return jsonify(optimization.to_dict())
    except Exception as e:
        logger.error(f"Error fetching AI optimization {optimization_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/analyze-backtest/<int:backtest_id>', methods=['POST'])
def analyze_backtest(backtest_id):
    """Analyze a backtest with AI and provide optimization recommendations."""
    try:
        backtest = BitunixBacktest.query.get_or_404(backtest_id)
        
        if backtest.status != 'completed':
            return jsonify({'error': 'Backtest must be completed for analysis'}), 400
        
        # Get current settings
        settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
        if not settings or not settings.ai_enabled:
            return jsonify({'error': 'AI analysis not enabled in settings'}), 400
        
        # Get optimization type from request
        data = request.get_json() or {}
        optimization_type = data.get('type', 'parameters')  # parameters, strategy, risk_management
        
        # Initialize AI optimizer
        optimizer = AIOptimizer(
            provider=settings.ai_provider,
            model=settings.ai_model
        )
        
        # Prepare backtest data for analysis
        backtest_data = {
            'results': backtest.to_dict(),
            'trade_history': json.loads(backtest.trade_history) if backtest.trade_history else [],
            'settings_used': json.loads(backtest.settings_snapshot) if backtest.settings_snapshot else {}
        }
        
        # Run AI analysis
        analysis_result = optimizer.analyze_performance(backtest_data, optimization_type)
        
        if analysis_result['success']:
            # Create optimization record
            optimization = BitunixAIOptimization(
                backtest_id=backtest_id,
                optimization_type=optimization_type,
                ai_provider=settings.ai_provider,
                ai_model=settings.ai_model,
                analysis_prompt=analysis_result['prompt'],
                ai_response=analysis_result['response'],
                recommended_settings=json.dumps(analysis_result['recommendations']),
                confidence_score=analysis_result.get('confidence_score', 0.5),
                expected_improvement=analysis_result.get('expected_improvement', 0)
            )
            
            db.session.add(optimization)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'optimization': optimization.to_dict(),
                'analysis': analysis_result
            })
        else:
            return jsonify({
                'success': False,
                'error': analysis_result.get('error', 'AI analysis failed')
            }), 500
            
    except Exception as e:
        logger.error(f"Error analyzing backtest {backtest_id}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/optimize-settings', methods=['POST'])
def optimize_settings():
    """Auto-optimize settings based on recent trading performance."""
    try:
        data = request.get_json() or {}
        
        # Get current settings
        settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
        if not settings or not settings.ai_enabled:
            return jsonify({'error': 'AI optimization not enabled in settings'}), 400
        
        # Get recent backtests for analysis
        recent_backtests = BitunixBacktest.query.filter_by(
            status='completed'
        ).order_by(BitunixBacktest.completed_at.desc()).limit(5).all()
        
        if not recent_backtests:
            return jsonify({'error': 'No completed backtests found for optimization'}), 400
        
        # Initialize AI optimizer
        optimizer = AIOptimizer(
            provider=settings.ai_provider,
            model=settings.ai_model
        )
        
        # Prepare data for optimization
        performance_data = []
        for backtest in recent_backtests:
            performance_data.append({
                'results': backtest.to_dict(),
                'settings': json.loads(backtest.settings_snapshot) if backtest.settings_snapshot else {}
            })
        
        # Run optimization
        optimization_result = optimizer.optimize_settings(
            performance_data, 
            current_settings=settings.to_dict(),
            optimization_goals=data.get('goals', ['maximize_profit', 'minimize_drawdown'])
        )
        
        if optimization_result['success']:
            # Create optimization record
            optimization = BitunixAIOptimization(
                optimization_type='auto_optimize',
                ai_provider=settings.ai_provider,
                ai_model=settings.ai_model,
                analysis_prompt=optimization_result['prompt'],
                ai_response=optimization_result['response'],
                recommended_settings=json.dumps(optimization_result['recommendations']),
                confidence_score=optimization_result.get('confidence_score', 0.5),
                expected_improvement=optimization_result.get('expected_improvement', 0)
            )
            
            db.session.add(optimization)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'optimization': optimization.to_dict(),
                'recommendations': optimization_result['recommendations'],
                'apply_url': f'/api/ai/optimizations/{optimization.id}/apply'
            })
        else:
            return jsonify({
                'success': False,
                'error': optimization_result.get('error', 'AI optimization failed')
            }), 500
            
    except Exception as e:
        logger.error(f"Error optimizing settings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/optimizations/<int:optimization_id>/apply', methods=['POST'])
def apply_optimization(optimization_id):
    """Apply AI optimization recommendations to current settings."""
    try:
        optimization = BitunixAIOptimization.query.get_or_404(optimization_id)
        
        if optimization.applied:
            return jsonify({'error': 'Optimization already applied'}), 400
        
        # Get current settings
        settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
        if not settings:
            return jsonify({'error': 'No settings found'}), 400
        
        # Parse recommendations
        recommendations = json.loads(optimization.recommended_settings)
        
        # Apply recommendations to settings
        applied_changes = []
        for key, value in recommendations.items():
            if hasattr(settings, key):
                old_value = getattr(settings, key)
                
                # Handle JSON fields
                if key in ['entry_distribution', 'target_distribution']:
                    setattr(settings, key, json.dumps(value))
                else:
                    setattr(settings, key, value)
                
                applied_changes.append({
                    'field': key,
                    'old_value': old_value,
                    'new_value': value
                })
        
        # Mark optimization as applied
        optimization.applied = True
        optimization.applied_at = db.func.now()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Optimization applied successfully',
            'applied_changes': applied_changes,
            'updated_settings': settings.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error applying optimization {optimization_id}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/suggestions', methods=['GET'])
def get_ai_suggestions():
    """Get AI suggestions for improving trading performance."""
    try:
        # Get current settings
        settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
        if not settings or not settings.ai_enabled:
            return jsonify({'error': 'AI suggestions not enabled in settings'}), 400
        
        # Get recent performance data
        recent_backtests = BitunixBacktest.query.filter_by(
            status='completed'
        ).order_by(BitunixBacktest.completed_at.desc()).limit(3).all()
        
        # Initialize AI optimizer
        optimizer = AIOptimizer(
            provider=settings.ai_provider,
            model=settings.ai_model
        )
        
        # Get general suggestions
        suggestions_result = optimizer.get_trading_suggestions(
            recent_performance=[bt.to_dict() for bt in recent_backtests],
            current_settings=settings.to_dict()
        )
        
        if suggestions_result['success']:
            return jsonify({
                'success': True,
                'suggestions': suggestions_result['suggestions'],
                'confidence': suggestions_result.get('confidence', 0.5),
                'generated_at': suggestions_result.get('timestamp')
            })
        else:
            return jsonify({
                'success': False,
                'error': suggestions_result.get('error', 'Failed to generate suggestions')
            }), 500
            
    except Exception as e:
        logger.error(f"Error getting AI suggestions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/market-analysis', methods=['POST'])
def analyze_market_conditions():
    """Analyze current market conditions and provide trading recommendations."""
    try:
        data = request.get_json() or {}
        coins = data.get('coins', ['BTC', 'ETH', 'SOL'])
        
        # Get current settings
        settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
        if not settings or not settings.ai_enabled:
            return jsonify({'error': 'AI market analysis not enabled in settings'}), 400
        
        # Initialize AI optimizer
        optimizer = AIOptimizer(
            provider=settings.ai_provider,
            model=settings.ai_model
        )
        
        # Run market analysis
        analysis_result = optimizer.analyze_market_conditions(coins)
        
        if analysis_result['success']:
            return jsonify({
                'success': True,
                'analysis': analysis_result['analysis'],
                'recommendations': analysis_result.get('recommendations', []),
                'market_sentiment': analysis_result.get('sentiment', 'neutral'),
                'timestamp': analysis_result.get('timestamp')
            })
        else:
            return jsonify({
                'success': False,
                'error': analysis_result.get('error', 'Market analysis failed')
            }), 500
            
    except Exception as e:
        logger.error(f"Error analyzing market conditions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/stats', methods=['GET'])
def get_ai_stats():
    """Get AI optimization statistics."""
    try:
        total_optimizations = BitunixAIOptimization.query.count()
        applied_optimizations = BitunixAIOptimization.query.filter_by(applied=True).count()
        
        # Count by optimization type
        type_stats = db.session.query(
            BitunixAIOptimization.optimization_type,
            db.func.count(BitunixAIOptimization.id).label('count')
        ).group_by(BitunixAIOptimization.optimization_type).all()
        
        # Average confidence score
        avg_confidence = db.session.query(
            db.func.avg(BitunixAIOptimization.confidence_score)
        ).scalar() or 0
        
        # Recent optimizations
        recent_optimizations = BitunixAIOptimization.query.order_by(
            BitunixAIOptimization.created_at.desc()
        ).limit(5).all()
        
        return jsonify({
            'total_optimizations': total_optimizations,
            'applied_optimizations': applied_optimizations,
            'pending_optimizations': total_optimizations - applied_optimizations,
            'type_distribution': [
                {'type': type_name, 'count': count} 
                for type_name, count in type_stats
            ],
            'average_confidence': round(float(avg_confidence), 2),
            'recent_optimizations': [opt.to_dict() for opt in recent_optimizations]
        })
        
    except Exception as e:
        logger.error(f"Error fetching AI stats: {str(e)}")
        return jsonify({'error': str(e)}), 500