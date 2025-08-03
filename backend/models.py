from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class BitunixSignal(db.Model):
    __tablename__ = 'bitunix_signals'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor = db.Column(db.String(50), default='bitunix', nullable=False)
    raw_text = db.Column(db.Text, nullable=False)
    coin = db.Column(db.String(20), nullable=False)
    pair = db.Column(db.String(20), nullable=False, default='USDT')
    position_type = db.Column(db.String(10), nullable=False)  # LONG/SHORT
    
    # Entry configuration
    entry_zones = db.Column(db.Text)  # JSON string of entry zones
    leverage = db.Column(db.Integer, default=1)
    cross_leverage = db.Column(db.Boolean, default=False)
    
    # Targets and stops
    targets = db.Column(db.Text)  # JSON string of targets
    stop_loss = db.Column(db.Float)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False)
    parse_errors = db.Column(db.Text)
    
    # Relationships
    trades = db.relationship('BitunixTrade', backref='signal', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'vendor': self.vendor,
            'coin': self.coin,
            'pair': self.pair,
            'position_type': self.position_type,
            'entry_zones': json.loads(self.entry_zones) if self.entry_zones else [],
            'leverage': self.leverage,
            'cross_leverage': self.cross_leverage,
            'targets': json.loads(self.targets) if self.targets else [],
            'stop_loss': self.stop_loss,
            'created_at': self.created_at.isoformat(),
            'processed': self.processed,
            'parse_errors': self.parse_errors
        }

class BitunixTrade(db.Model):
    __tablename__ = 'bitunix_trades'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor = db.Column(db.String(50), default='bitunix', nullable=False)
    signal_id = db.Column(db.Integer, db.ForeignKey('bitunix_signals.id'), nullable=False)
    
    # Trade details
    coin = db.Column(db.String(20), nullable=False)
    pair = db.Column(db.String(20), nullable=False, default='USDT')
    position_type = db.Column(db.String(10), nullable=False)
    size = db.Column(db.Float, nullable=False)
    leverage = db.Column(db.Integer, default=1)
    
    # Entry details
    entry_price = db.Column(db.Float)
    entry_orders = db.Column(db.Text)  # JSON string of order IDs
    entry_filled = db.Column(db.Float, default=0.0)
    
    # Exit details
    target_prices = db.Column(db.Text)  # JSON string of target prices
    target_orders = db.Column(db.Text)  # JSON string of target order IDs
    stop_loss_price = db.Column(db.Float)
    stop_loss_order_id = db.Column(db.String(100))
    
    # Status tracking
    status = db.Column(db.String(20), default='pending')  # pending, active, partially_filled, closed, cancelled
    pnl = db.Column(db.Float, default=0.0)
    pnl_percentage = db.Column(db.Float, default=0.0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    closed_at = db.Column(db.DateTime)
    
    # Error handling
    errors = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'vendor': self.vendor,
            'signal_id': self.signal_id,
            'coin': self.coin,
            'pair': self.pair,
            'position_type': self.position_type,
            'size': self.size,
            'leverage': self.leverage,
            'entry_price': self.entry_price,
            'entry_orders': json.loads(self.entry_orders) if self.entry_orders else [],
            'entry_filled': self.entry_filled,
            'target_prices': json.loads(self.target_prices) if self.target_prices else [],
            'target_orders': json.loads(self.target_orders) if self.target_orders else [],
            'stop_loss_price': self.stop_loss_price,
            'stop_loss_order_id': self.stop_loss_order_id,
            'status': self.status,
            'pnl': self.pnl,
            'pnl_percentage': self.pnl_percentage,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'errors': self.errors
        }

class BitunixSettings(db.Model):
    __tablename__ = 'bitunix_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor = db.Column(db.String(50), default='bitunix', nullable=False)
    
    # API Configuration
    api_key = db.Column(db.String(255))
    api_secret = db.Column(db.String(255))
    api_passphrase = db.Column(db.String(255))
    testnet = db.Column(db.Boolean, default=True)
    
    # Trading Configuration
    default_leverage = db.Column(db.Integer, default=1)
    default_position_size = db.Column(db.Float, default=10.0)  # USDT
    max_position_size = db.Column(db.Float, default=1000.0)  # USDT
    risk_percentage = db.Column(db.Float, default=2.0)  # % of account per trade
    
    # Entry Configuration
    entry_steps = db.Column(db.Integer, default=3)
    entry_distribution = db.Column(db.Text)  # JSON: [40, 35, 25] percentages
    
    # Exit Configuration
    target_distribution = db.Column(db.Text)  # JSON: [50, 30, 20] percentages
    auto_stop_loss = db.Column(db.Boolean, default=True)
    trailing_stop = db.Column(db.Boolean, default=False)
    trailing_stop_percentage = db.Column(db.Float, default=5.0)
    
    # Automation
    auto_trade = db.Column(db.Boolean, default=False)
    require_confirmation = db.Column(db.Boolean, default=True)
    
    # Notifications
    email_notifications = db.Column(db.Boolean, default=True)
    email_address = db.Column(db.String(255))
    
    # AI Configuration
    ai_provider = db.Column(db.String(50), default='openai')  # openai, anthropic
    ai_model = db.Column(db.String(100), default='gpt-4')
    ai_enabled = db.Column(db.Boolean, default=False)
    auto_optimize = db.Column(db.Boolean, default=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'vendor': self.vendor,
            'api_key': self.api_key[:8] + '...' if self.api_key else None,  # Masked for security
            'testnet': self.testnet,
            'default_leverage': self.default_leverage,
            'default_position_size': self.default_position_size,
            'max_position_size': self.max_position_size,
            'risk_percentage': self.risk_percentage,
            'entry_steps': self.entry_steps,
            'entry_distribution': json.loads(self.entry_distribution) if self.entry_distribution else [40, 35, 25],
            'target_distribution': json.loads(self.target_distribution) if self.target_distribution else [50, 30, 20],
            'auto_stop_loss': self.auto_stop_loss,
            'trailing_stop': self.trailing_stop,
            'trailing_stop_percentage': self.trailing_stop_percentage,
            'auto_trade': self.auto_trade,
            'require_confirmation': self.require_confirmation,
            'email_notifications': self.email_notifications,
            'email_address': self.email_address,
            'ai_provider': self.ai_provider,
            'ai_model': self.ai_model,
            'ai_enabled': self.ai_enabled,
            'auto_optimize': self.auto_optimize,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class BitunixBacktest(db.Model):
    __tablename__ = 'bitunix_backtests'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor = db.Column(db.String(50), default='bitunix', nullable=False)
    name = db.Column(db.String(200), nullable=False)
    
    # Backtest parameters
    signals_data = db.Column(db.Text)  # JSON string of signals
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    initial_balance = db.Column(db.Float, default=1000.0)
    
    # Configuration used
    settings_snapshot = db.Column(db.Text)  # JSON snapshot of settings
    
    # Results
    final_balance = db.Column(db.Float)
    total_pnl = db.Column(db.Float)
    total_pnl_percentage = db.Column(db.Float)
    total_trades = db.Column(db.Integer)
    winning_trades = db.Column(db.Integer)
    losing_trades = db.Column(db.Integer)
    win_rate = db.Column(db.Float)
    max_drawdown = db.Column(db.Float)
    sharpe_ratio = db.Column(db.Float)
    
    # Detailed results
    trade_history = db.Column(db.Text)  # JSON string of all trades
    equity_curve = db.Column(db.Text)  # JSON string of equity over time
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    
    def to_dict(self):
        return {
            'id': self.id,
            'vendor': self.vendor,
            'name': self.name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'initial_balance': self.initial_balance,
            'final_balance': self.final_balance,
            'total_pnl': self.total_pnl,
            'total_pnl_percentage': self.total_pnl_percentage,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.status
        }

class BitunixAIOptimization(db.Model):
    __tablename__ = 'bitunix_ai_optimizations'
    
    id = db.Column(db.Integer, primary_key=True)
    vendor = db.Column(db.String(50), default='bitunix', nullable=False)
    
    # Input data
    backtest_id = db.Column(db.Integer, db.ForeignKey('bitunix_backtests.id'))
    optimization_type = db.Column(db.String(50))  # parameters, strategy, risk_management
    
    # AI Analysis
    ai_provider = db.Column(db.String(50))
    ai_model = db.Column(db.String(100))
    analysis_prompt = db.Column(db.Text)
    ai_response = db.Column(db.Text)
    
    # Recommendations
    recommended_settings = db.Column(db.Text)  # JSON string
    confidence_score = db.Column(db.Float)
    expected_improvement = db.Column(db.Float)
    
    # Implementation
    applied = db.Column(db.Boolean, default=False)
    applied_at = db.Column(db.DateTime)
    performance_after = db.Column(db.Text)  # JSON string of performance metrics
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'vendor': self.vendor,
            'backtest_id': self.backtest_id,
            'optimization_type': self.optimization_type,
            'ai_provider': self.ai_provider,
            'ai_model': self.ai_model,
            'recommended_settings': json.loads(self.recommended_settings) if self.recommended_settings else {},
            'confidence_score': self.confidence_score,
            'expected_improvement': self.expected_improvement,
            'applied': self.applied,
            'applied_at': self.applied_at.isoformat() if self.applied_at else None,
            'created_at': self.created_at.isoformat()
        }