from flask import request, jsonify
from app.api import bp
from app.services.upload_service import upload_experiment_service, validate_upload_service
from app.utils.decorators import validate_json
from app.utils.api_auth import require_api_key
import logging


@bp.route('/upload/experiment', methods=['POST'])
@require_api_key
@validate_json(['unique_id', 'test_class_name', 'configuration', 'trials'])
def upload_experiment():
    """Upload experiment data from Android app"""
    try:
        data = request.get_json()

        # Extract fields
        unique_id = data.get('unique_id', '')
        test_class_name = data.get('test_class_name', '')
        configuration = data.get('configuration', {})
        trials = data.get('trials', [])
        device_id = data.get('device_id', '')

        # Use service to upload experiment
        success, result, error_code = upload_experiment_service(
            unique_id=unique_id,
            test_class_name=test_class_name,
            configuration=configuration,
            trials=trials,
            device_id=device_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        
        if not success:
            return jsonify({'error': result}), error_code
        
        return jsonify(result), 201
        
    except Exception as e:
        logging.error(f"Upload experiment error: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@bp.route('/upload/validate', methods=['POST'])
@require_api_key
@validate_json(['test_class_name', 'configuration'])
def validate_upload():
    """Validate experiment data before upload"""
    try:
        data = request.get_json()
        
        test_class_name = data.get('test_class_name', '')
        configuration = data.get('configuration', {})
        
        # Use service to validate upload
        success, result, error_code = validate_upload_service(test_class_name, configuration)
        
        if not success:
            return jsonify({
                'valid': False,
                'error': result
            }), 200
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Validate upload error: {e}")
        return jsonify({'error': 'Internal server error'}), 500





@bp.route('/upload/status', methods=['GET'])
def upload_status():
    """Get upload service status"""
    try:
        # Use service to get upload status
        from app.services.upload_service import get_upload_status_service
        success, result, error_code = get_upload_status_service()
        
        if not success:
            return jsonify({
                'status': 'unhealthy',
                'error': result
            }), error_code or 500
        
        return jsonify(result), 200
        
    except Exception as e:
        logging.error(f"Upload status error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': 'Internal server error'
        }), 500


@bp.route('/upload/auth-info', methods=['GET'])
@require_api_key
def auth_info():
    """Get API authentication information (for debugging)"""
    try:
        from app.utils.api_auth import get_api_key_info
        info = get_api_key_info()
        
        return jsonify({
            'authentication': 'API Key required',
            'methods': [
                'Header: X-API-Key: your-api-key',
                'Header: Authorization: Bearer your-api-key',
                'Query: ?api_key=your-api-key',
                'JSON body: {"api_key": "your-api-key"}'
            ],
            'config': info
        }), 200
        
    except Exception as e:
        logging.error(f"Auth info error: {e}")
        return jsonify({'error': 'Internal server error'}), 500