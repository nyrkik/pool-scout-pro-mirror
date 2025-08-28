#!/usr/bin/env python3
"""
Flask Application with Enterprise Logging and Search Reports
"""

import os
import sys
import logging
import logging.config
import yaml
import time
import socket
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, request, g, redirect
from werkzeug.middleware.proxy_fix import ProxyFix

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

class PerformanceMiddleware:
    """Middleware to log request performance metrics"""
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger('performance')

    def __call__(self, environ, start_response):
        start_time = time.time()

        def new_start_response(status, response_headers, exc_info=None):
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # ms
            self.logger.info({
                'timestamp': datetime.utcnow().isoformat(),
                'method': environ.get('REQUEST_METHOD'),
                'path': environ.get('PATH_INFO'),
                'status_code': status.split()[0],
                'response_time_ms': round(response_time, 2),
                'remote_addr': environ.get('REMOTE_ADDR'),
                'user_agent': environ.get('HTTP_USER_AGENT', ''),
                'content_length': environ.get('CONTENT_LENGTH', 0)
            })
            return start_response(status, response_headers, exc_info)

        return self.app(environ, new_start_response)

def setup_logging():
    """Setup enterprise logging configuration"""
    log_dir = Path('data/logs')
    log_dir.mkdir(parents=True, exist_ok=True)

    config_path = Path('config/logging_config.yaml')
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            logging.config.dictConfig(config)
    else:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(name)s | %(levelname)s | %(message)s',
            handlers=[logging.StreamHandler(), logging.FileHandler('data/logs/pool_scout_pro.log')]
        )

    logger = logging.getLogger('pool_scout_pro')
    logger.info("🚀 Enterprise logging system initialized")
    return logger

def create_app():
    """Create and configure Flask app with enterprise features"""
    logger = logging.getLogger('pool_scout_pro')

    app = Flask(
        __name__,
        template_folder='../../templates',
        static_folder='../../templates/static'
    )
    app.config['SECRET_KEY'] = 'your-secret-key-here'

    # Reverse proxy fix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Performance middleware
    app.wsgi_app = PerformanceMiddleware(app.wsgi_app)

    # Request timing
    @app.before_request
    def before_request():
        g.start_time = time.time()
        logger.debug(f"🔥 REQUEST START: {request.method} {request.path}")

    @app.after_request
    def after_request(response):
        if hasattr(g, 'start_time'):
            duration = (time.time() - g.start_time) * 1000
            logger.debug(f"✅ REQUEST END: {request.method} {request.path} - {response.status_code} ({duration:.2f}ms)")
        return response

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        logging.getLogger('errors').error(f"404 Not Found: {request.path} from {request.remote_addr}")
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        logging.getLogger('errors').error(f"500 Internal Error: {request.path} - {str(error)}")
        return jsonify({'error': 'Internal server error'}), 500

    # Blueprints
    try:
        from web.routes.api_routes import api_routes
        from web.routes.downloads import bp as downloads_api

        app.register_blueprint(api_routes)
        app.register_blueprint(downloads_api)

        logger.info("✅ API routes registered successfully")
        logger.info("✅ Downloads API registered successfully")
    except Exception as e:
        logger.error(f"❌ Failed to register routes: {e}")
        raise

    # Main routes
    @app.route('/')
    def index():
        logger.info(f"📱 Index page accessed from {request.remote_addr}")
        return redirect('/search-reports')

    @app.route('/search-reports')
    def search_reports():
        logger.info(f"📋 Search reports page accessed from {request.remote_addr}")
        return render_template('search_reports.html')

    @app.route('/health')
    def health():
        health_info = {
            'status': 'healthy',
            'service': 'pool_scout_pro',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0',
            'hostname': socket.gethostname(),
            'uptime_seconds': time.time() - app.start_time if hasattr(app, 'start_time') else 0
        }
        logger.debug(f"🏥 Health check from {request.remote_addr}")
        return jsonify(health_info)

    app.start_time = time.time()
    return app
