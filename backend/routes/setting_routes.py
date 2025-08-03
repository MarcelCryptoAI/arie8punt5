from flask import Blueprint, request, jsonify
from models import BitunixSettings, db
from services.bitunix_api import BitunixAPI
import json
import logging
from cryptography.fernet import Fernet
import os

logger = logging.getLogger(__name__)

bp = Blueprint('settings', __name__, url_prefix='/api/settings')

def encrypt_api_key(api_key: str) -> str:
    """Encrypt API key for secure storage."""
    if not api_key:
        return api_key
    
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        # Generate a key if not provided (for development)
        key = Fernet.generate_key()
        logger.warning("No encryption key found, using generated key")
    
    if isinstance(key, str):
        key = key.encode()
    
    f = Fernet(key)
    return f.encrypt(api_key.encode()).decode()

def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt API key for use."""
    if not encrypted_key:
        return encrypted_key
    
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        return encrypted_key  # Return as-is if no encryption key
    
    if isinstance(key, str):
        key = key.encode()
    
    try:
        f = Fernet(key)
        return f.decrypt(encrypted_key.encode()).decode()
    except Exception:
        return encrypted_key  # Return as-is if decryption fails

@bp.route('/', methods=['GET'])
def get_settings():
    """Get current settings."""
    try:
        settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
        
        if not settings:
            # Create default settings
            settings = BitunixSettings(vendor='bitunix')
            db.session.add(settings)
            db.session.commit()
        
        return jsonify(settings.to_dict())
        
    except Exception as e:
        logger.error(f"Error fetching settings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/', methods=['PUT'])
def update_settings():
    """Update settings."""
    try:
        data = request.get_json()
        settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
        
        if not settings:
            settings = BitunixSettings(vendor='bitunix')
            db.session.add(settings)
        
        # Update API configuration
        if 'api_key' in data:
            settings.api_key = encrypt_api_key(data['api_key'])
        if 'api_secret' in data:
            settings.api_secret = encrypt_api_key(data['api_secret'])
        if 'api_passphrase' in data:
            settings.api_passphrase = encrypt_api_key(data['api_passphrase'])
        if 'testnet' in data:
            settings.testnet = data['testnet']
        
        # Update trading configuration
        if 'default_leverage' in data:
            settings.default_leverage = data['default_leverage']
        if 'default_position_size' in data:
            settings.default_position_size = data['default_position_size']
        if 'max_position_size' in data:
            settings.max_position_size = data['max_position_size']
        if 'risk_percentage' in data:
            settings.risk_percentage = data['risk_percentage']
        
        # Update entry configuration
        if 'entry_steps' in data:
            settings.entry_steps = data['entry_steps']
        if 'entry_distribution' in data:
            settings.entry_distribution = json.dumps(data['entry_distribution'])
        
        # Update exit configuration
        if 'target_distribution' in data:
            settings.target_distribution = json.dumps(data['target_distribution'])
        if 'auto_stop_loss' in data:
            settings.auto_stop_loss = data['auto_stop_loss']
        if 'trailing_stop' in data:
            settings.trailing_stop = data['trailing_stop']
        if 'trailing_stop_percentage' in data:
            settings.trailing_stop_percentage = data['trailing_stop_percentage']
        
        # Update automation
        if 'auto_trade' in data:
            settings.auto_trade = data['auto_trade']
        if 'require_confirmation' in data:
            settings.require_confirmation = data['require_confirmation']
        
        # Update notifications
        if 'email_notifications' in data:
            settings.email_notifications = data['email_notifications']
        if 'email_address' in data:
            settings.email_address = data['email_address']
        
        # Update AI configuration
        if 'ai_provider' in data:
            settings.ai_provider = data['ai_provider']
        if 'ai_model' in data:
            settings.ai_model = data['ai_model']
        if 'ai_enabled' in data:
            settings.ai_enabled = data['ai_enabled']
        if 'auto_optimize' in data:
            settings.auto_optimize = data['auto_optimize']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'settings': settings.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/test-connection', methods=['POST'])
def test_api_connection():
    """Test Bitunix API connection."""
    try:
        settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
        
        if not settings or not settings.api_key:
            return jsonify({'error': 'API credentials not configured'}), 400
        
        # Decrypt credentials for testing
        api_key = decrypt_api_key(settings.api_key)
        api_secret = decrypt_api_key(settings.api_secret)
        api_passphrase = decrypt_api_key(settings.api_passphrase)
        
        # Test API connection
        api = BitunixAPI(api_key, api_secret, api_passphrase, settings.testnet)
        
        try:
            account_info = api.get_account_info()
            balance = api.get_balance()
            
            return jsonify({
                'success': True,
                'message': 'API connection successful',
                'account_info': account_info,
                'balance': balance
            })
            
        except Exception as api_error:
            return jsonify({
                'success': False,
                'error': f'API connection failed: {str(api_error)}'
            }), 400
        
    except Exception as e:
        logger.error(f"Error testing API connection: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/presets', methods=['GET'])
def get_presets():
    """Get trading presets for different strategies."""
    presets = {
        'conservative': {
            'name': 'Conservative',
            'description': 'Low risk, steady gains',
            'default_leverage': 2,
            'risk_percentage': 1.0,
            'entry_steps': 3,
            'entry_distribution': [50, 30, 20],
            'target_distribution': [60, 25, 15],
            'auto_stop_loss': True,
            'trailing_stop': False
        },
        'moderate': {
            'name': 'Moderate',
            'description': 'Balanced risk/reward',
            'default_leverage': 5,
            'risk_percentage': 2.0,
            'entry_steps': 3,
            'entry_distribution': [40, 35, 25],
            'target_distribution': [50, 30, 20],
            'auto_stop_loss': True,
            'trailing_stop': True,
            'trailing_stop_percentage': 5.0
        },
        'aggressive': {
            'name': 'Aggressive',
            'description': 'High risk, high reward',
            'default_leverage': 10,
            'risk_percentage': 3.0,
            'entry_steps': 2,
            'entry_distribution': [60, 40],
            'target_distribution': [40, 35, 25],
            'auto_stop_loss': True,
            'trailing_stop': True,
            'trailing_stop_percentage': 3.0
        },
        'scalping': {
            'name': 'Scalping',
            'description': 'Quick small profits',
            'default_leverage': 15,
            'risk_percentage': 1.5,
            'entry_steps': 1,
            'entry_distribution': [100],
            'target_distribution': [70, 30],
            'auto_stop_loss': True,
            'trailing_stop': True,
            'trailing_stop_percentage': 2.0
        }
    }
    
    return jsonify({'presets': presets})

@bp.route('/presets/<preset_name>', methods=['POST'])
def apply_preset(preset_name):
    """Apply a trading preset."""
    try:
        # Get preset configuration
        presets_response = get_presets()
        presets = presets_response.get_json()['presets']
        
        if preset_name not in presets:
            return jsonify({'error': 'Preset not found'}), 404
        
        preset = presets[preset_name]
        
        # Get current settings
        settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
        if not settings:
            settings = BitunixSettings(vendor='bitunix')
            db.session.add(settings)
        
        # Apply preset values
        settings.default_leverage = preset['default_leverage']
        settings.risk_percentage = preset['risk_percentage']
        settings.entry_steps = preset['entry_steps']
        settings.entry_distribution = json.dumps(preset['entry_distribution'])
        settings.target_distribution = json.dumps(preset['target_distribution'])
        settings.auto_stop_loss = preset['auto_stop_loss']
        settings.trailing_stop = preset['trailing_stop']
        
        if 'trailing_stop_percentage' in preset:
            settings.trailing_stop_percentage = preset['trailing_stop_percentage']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Applied {preset["name"]} preset',
            'settings': settings.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error applying preset {preset_name}: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/backup', methods=['GET'])
def backup_settings():
    """Export settings as backup."""
    try:
        settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
        
        if not settings:
            return jsonify({'error': 'No settings found'}), 404
        
        # Create backup (exclude sensitive API keys)
        backup_data = settings.to_dict()
        backup_data['api_key'] = None
        backup_data['api_secret'] = None
        backup_data['api_passphrase'] = None
        
        return jsonify({
            'success': True,
            'backup': backup_data,
            'timestamp': settings.updated_at.isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error creating settings backup: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/restore', methods=['POST'])
def restore_settings():
    """Restore settings from backup."""
    try:
        data = request.get_json()
        backup_data = data.get('backup')
        
        if not backup_data:
            return jsonify({'error': 'Backup data required'}), 400
        
        settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
        if not settings:
            settings = BitunixSettings(vendor='bitunix')
            db.session.add(settings)
        
        # Restore non-sensitive settings
        restore_fields = [
            'default_leverage', 'default_position_size', 'max_position_size',
            'risk_percentage', 'entry_steps', 'entry_distribution',
            'target_distribution', 'auto_stop_loss', 'trailing_stop',
            'trailing_stop_percentage', 'auto_trade', 'require_confirmation',
            'email_notifications', 'email_address', 'ai_provider',
            'ai_model', 'ai_enabled', 'auto_optimize'
        ]
        
        for field in restore_fields:
            if field in backup_data:
                setattr(settings, field, backup_data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Settings restored successfully',
            'settings': settings.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error restoring settings: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/reset', methods=['POST'])
def reset_settings():
    """Reset settings to defaults."""
    try:
        settings = BitunixSettings.query.filter_by(vendor='bitunix').first()
        
        if settings:
            db.session.delete(settings)
        
        # Create new default settings
        new_settings = BitunixSettings(vendor='bitunix')
        db.session.add(new_settings)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Settings reset to defaults',
            'settings': new_settings.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error resetting settings: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500