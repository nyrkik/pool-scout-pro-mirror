"""
Downloads API Routes - non-blocking starter
Accepts both /api/v1/downloads/start and /api/downloads/start
CLEAN VERSION: Uses service factory pattern consistently
"""

from flask import Blueprint, request, jsonify
import threading
import logging
import sys
import os

# Add src to path for service factory imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from web.shared.services import get_pdf_downloader

# Note: blueprint is rooted at /api so we can define both /v1/downloads/start and /downloads/start
bp = Blueprint('downloads', __name__, url_prefix='/api')
logger = logging.getLogger('pool_scout_pro')

def _run_downloads(facilities):
    try:
        # Use factory pattern instead of direct instantiation
        downloader = get_pdf_downloader()
        result = downloader.download_pdfs_from_facilities(facilities or [])
        logger.info("Download job finished: %s", {
            'successful': result.get('successful'),
            'failed': result.get('failed')
        })
    except Exception as e:
        logger.exception("Background download job crashed: %s", e)

def _start_download_impl():
    payload = request.get_json(silent=True) or {}
    facilities = payload.get('facilities') or []
    logger.info("▶️ /downloads/start called – starting background job for %d facilities", len(facilities))

    t = threading.Thread(target=_run_downloads, args=(facilities,), daemon=True)
    t.start()

    return jsonify({
        'success': True,
        'message': 'Download started',
        'started_count': len(facilities)
    }), 200

@bp.route('/v1/downloads/start', methods=['POST'])
def start_download_v1():
    return _start_download_impl()

@bp.route('/downloads/start', methods=['POST'])
def start_download_legacy():
    return _start_download_impl()
