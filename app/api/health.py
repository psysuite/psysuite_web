from flask import jsonify
from datetime import datetime
from app.api import bp
from app.models.user import User
from app.models.test import Test
from app.models.experiment import Experiment
from app import db
import logging


@bp.route('/health', methods=['GET'])
def health_check():
    """System health check endpoint"""
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        # Get basic system stats
        stats = {
            'users': User.query.count(),
            'tests': Test.query.count(),
            'experiments': Experiment.query.count(),
            'production_tests': Test.query.filter_by(status='production').count()
        }
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'stats': stats
        }), 200
        
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'disconnected',
            'error': str(e)
        }), 500


@bp.route('/status', methods=['GET'])
def system_status():
    """Detailed system status (admin only in production)"""
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        # Get detailed stats
        total_users = User.query.count()
        admin_users = User.query.filter_by(role='admin').count()
        researcher_users = User.query.filter_by(role='researcher').count()
        active_users = User.query.filter_by(is_active=True).count()
        
        total_tests = Test.query.count()
        dev_tests = Test.query.filter_by(status='development').count()
        prod_tests = Test.query.filter_by(status='production').count()
        final_tests = Test.query.filter_by(status='finalized').count()
        
        total_experiments = Experiment.query.count()
        completed_experiments = Experiment.query.filter_by(completion_status='completed').count()
        
        # Recent activity
        recent_experiments = Experiment.query.order_by(db.desc(Experiment.uploaded_at)).limit(5).all()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'users': {
                'total': total_users,
                'admin': admin_users,
                'researcher': researcher_users,
                'active': active_users
            },
            'tests': {
                'total': total_tests,
                'development': dev_tests,
                'production': prod_tests,
                'finalized': final_tests
            },
            'experiments': {
                'total': total_experiments,
                'completed': completed_experiments,
                'completion_rate': round((completed_experiments / total_experiments * 100), 2) if total_experiments > 0 else 0
            },
            'recent_activity': [
                {
                    'experiment_id': exp.id,
                    'test_name': exp.test.name,
                    'subject': exp.subject_label,
                    'uploaded_at': exp.uploaded_at.isoformat() if exp.uploaded_at else None
                }
                for exp in recent_experiments
            ]
        }), 200
        
    except Exception as e:
        logging.error(f"Status check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'disconnected',
            'error': str(e)
        }), 500