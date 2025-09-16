from flask import Blueprint, jsonify, request
import sqlite3
from src.web.shared.services import get_database_service, get_search_service, get_pdf_downloader, get_download_progress_service_factory
from src.core.error_handler import ErrorHandler
from services.search_progress_service import SearchProgressService
from core.database_config import db_config

api_routes = Blueprint('api', __name__, url_prefix='/api/v1')

db_service = get_database_service()
search_service = get_search_service()
error_handler = ErrorHandler()

# Track last searched date for change detection
last_searched_date = None

@api_routes.route('/reports/saved/<search_date>', methods=['GET'])
def get_saved_reports_for_date(search_date):
    """API endpoint to get existing reports for a given date from the database."""
    search_service = get_search_service()
    result = search_service.get_saved_reports_by_date(search_date)
    return jsonify(result)

@api_routes.route("/reports/existing-for-date", methods=["POST"])
def get_existing_reports_for_date():
    try:
        data = request.get_json()
        search_date = data.get('date')
        
        # ADD LOGGING: Log the existing reports request
        error_handler.log_info("API Existing Reports Request", f"Checking existing reports for {search_date}", {
            'date': search_date,
            'endpoint': 'existing-for-date'
        })
        
        reports = db_service.get_reports_by_date(search_date)
        enriched_reports = []
        
        if reports:
            for report in reports:
                facility = db_service.get_facility_by_id(report.get('facility_id'))
                if facility:
                    violations = db_service.get_violations_for_report(report.get('id'))
                    report['facility'] = facility
                    report['violations'] = violations or []
                    enriched_reports.append(report)
        
        # ADD LOGGING: Log the results with facility names
        facility_names = [report.get('facility', {}).get('name', 'Unknown') for report in enriched_reports]
        error_handler.log_info("API Existing Reports Result", f"Found {len(enriched_reports)} existing reports for {search_date}", {
            'date': search_date,
            'existing_count': len(enriched_reports),
            'facility_names': facility_names
        })
        
        print(f"📊 API: {len(enriched_reports)} existing reports for {search_date}")
        if facility_names:
            print(f"📋 API: Existing facilities: {', '.join(facility_names[:5])}{'...' if len(facility_names) > 5 else ''}")
        
        return jsonify({
            "success": True, 
            "reports": enriched_reports, 
            "saved_count": len(enriched_reports)
        })
    except Exception as e:
        error_handler.log_error("Get Existing Reports API Error", str(e))
        return jsonify({"success": False, "message": "An unexpected error occurred."}), 500

@api_routes.route("/reports/search-with-duplicates", methods=["POST"])
def search_with_duplicates():
    global last_searched_date
    
    try:
        print("🔍 SEARCH START: API endpoint called")
        
        data = request.get_json()
        start_date = data.get("start_date")
        
        # ADD LOGGING: Date change detection
        if last_searched_date != start_date:
            if last_searched_date:
                error_handler.log_info("API Date Change", f"Search date changed from {last_searched_date} to {start_date}", {
                    'previous_date': last_searched_date,
                    'new_date': start_date,
                    'endpoint': 'search-with-duplicates'
                })
                print(f"📅 API: Date changed {last_searched_date} → {start_date}")
            else:
                error_handler.log_info("API Initial Date", f"Initial search date set to {start_date}", {
                    'initial_date': start_date,
                    'endpoint': 'search-with-duplicates'
                })
                print(f"📅 API: Initial search date: {start_date}")
            
            last_searched_date = start_date
        
        print(f"📅 SEARCH START: Searching for date: {start_date}")
        
        # ADD LOGGING: Log search request
        error_handler.log_info("API Search Request", f"EMD search requested for {start_date}", {
            'start_date': start_date,
            'endpoint': 'search-with-duplicates'
        })
        
        # Get enhanced search data with EMD duplicate info
        print("🌐 SEARCH START: Calling search_service.search_emd_for_date")
        # Initialize search progress tracking
        progress_service = SearchProgressService()
        progress_service.start_search(start_date)
        
        search_data = search_service.search_emd_for_date(start_date)
        
        # Complete search progress tracking
        
        facilities = search_data.get('facilities', [])
        
        # Complete search progress tracking
        progress_service.complete_search(len(facilities))
        emd_duplicate_count = search_data.get('emd_duplicate_count', 0)
        emd_duplicate_names = search_data.get('emd_duplicate_names', [])
        
        print(f"📊 SEARCH START: Found {len(facilities)} facilities")
        print(f"📄 SEARCH START: EMD duplicates: {emd_duplicate_count}")
        
        # Create count data from facilities list
        total_reports = len(facilities) if facilities else 0
        duplicate_count = sum(1 for f in facilities if f.get('saved')) if facilities else 0
        
        # ADD LOGGING: Log search results with facility names
        facility_names = [f.get('name', 'Unknown') for f in facilities]
        error_handler.log_info("API Search Complete", f"EMD search completed: {total_reports} facilities found", {
            'start_date': start_date,
            'total_facilities': total_reports,
            'duplicate_count': duplicate_count,
            'emd_duplicate_count': emd_duplicate_count,
            'facility_names': facility_names,
            'emd_duplicate_names': emd_duplicate_names
        })
        
        print(f"✅ SEARCH START: Returning {total_reports} total, {duplicate_count} duplicates")
        if facility_names:
            print(f"🏢 API: Found facilities: {', '.join(facility_names[:5])}{'...' if len(facility_names) > 5 else ''}")
        
        return jsonify({
            "success": True, 
            "search_date": start_date, 
            "facilities": facilities or [],
            "total_reports": total_reports, 
            "duplicate_count": duplicate_count,
            "emd_duplicate_count": emd_duplicate_count,
            "emd_duplicate_names": emd_duplicate_names
        })
    except Exception as e:
        print(f"💥 SEARCH START: Exception occurred: {str(e)}")
        import traceback
        print("📋 SEARCH START: Full traceback:")
        traceback.print_exc()
        error_handler.log_error("Search with Duplicates API Error", str(e))
        return jsonify({"success": False, "message": "An unexpected error occurred."}), 500

@api_routes.route('/reports/download/start', methods=['POST'])
def start_download():
    try:
        print("🚀 DOWNLOAD START: API endpoint called")
        print("🚀 DOWNLOAD STEP 1: Getting request data")
        
        data = request.get_json()
        print("🚀 DOWNLOAD STEP 2: Request data retrieved")
        
        facilities = data.get('facilities', [])
        print(f"🔧 DEBUG: Received facilities type: {type(facilities)}, length: {len(facilities) if hasattr(facilities, '__len__') else 'no len'}")
        
        # ADD LOGGING: Log download request with facility names
        facility_names = [f.get('name', 'Unknown') for f in facilities]
        error_handler.log_info("API Download Request", f"Download requested for {len(facilities)} facilities", {
            'facility_count': len(facilities),
            'facility_names': facility_names,
            'endpoint': 'download/start'
        })
        
        print(f"📊 DOWNLOAD START: Received {len(facilities)} facilities")
        print(f"🏢 API: Download requested for: {', '.join(facility_names[:5])}{'...' if len(facility_names) > 5 else ''}")
        
        if not facilities:
            print("❌ DOWNLOAD START: No facilities provided")
            return jsonify({"success": False, "message": "No facilities to download."}), 400
        
        print("🔧 DOWNLOAD START: Getting shared driver")
        shared_driver = search_service.get_shared_driver()
        print(f"🔧 API DEBUG: shared_driver = {shared_driver}")
        print(f"🔧 API DEBUG: shared_driver type = {type(shared_driver)}")
        downloader_with_session = get_pdf_downloader(shared_driver)
        print(f"🔧 API DEBUG: downloader_with_session = {downloader_with_session}")
        
        print("🔧 DOWNLOAD START: Calling download_pdfs_from_facilities")
        results = downloader_with_session.download_pdfs_from_facilities(facilities)
        
        # ADD LOGGING: Log download completion
        successful = results.get('successful', 0)
        failed = results.get('failed', 0)
        error_handler.log_info("API Download Complete", f"Download completed: {successful} successful, {failed} failed", {
            'successful_count': successful,
            'failed_count': failed,
            'total_requested': len(facilities),
            'job_id': results.get('job_id'),
            'requested_facilities': facility_names
        })
        
        print(f"✅ DOWNLOAD START: Download completed with results: {results}")
        print(f"📊 API: Download complete - {successful} successful, {failed} failed")
        
        return jsonify({"success": True, "results": results})
        
    except Exception as e:
        print(f"💥 DOWNLOAD START: Exception occurred: {str(e)}")
        import traceback
        print("📋 DOWNLOAD START: Full traceback:")
        traceback.print_exc()
        error_handler.log_error("Download Start API Error", str(e))
        return jsonify({"success": False, "message": "An unexpected error occurred."}), 500

@api_routes.route('/downloads/progress', methods=['GET'])
def download_progress():
    try:
        progress_data = get_download_progress_service_factory().get_progress()
        return jsonify({
            "success": True,
            "progress": progress_data
        })
    except Exception as e:
        error_handler.log_error("Download Progress API Error", str(e))
        return jsonify({"success": False, "message": "An unexpected error occurred."}), 500

# MANAGEMENT ENDPOINTS - Added for Sapphire Pool Service facility tracking

@api_routes.route('/facilities/<int:facility_id>/management', methods=['GET'])
def get_facility_management(facility_id):
    """Get management information for a facility"""
    try:
        conn = sqlite3.connect(db_config.inspection_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, sapphire_managed, management_company
            FROM facilities 
            WHERE id = ?
        """, (facility_id,))
        
        facility = cursor.fetchone()
        conn.close()
        
        if not facility:
            return jsonify({'success': False, 'message': 'Facility not found'}), 404
            
        return jsonify({
            'success': True,
            'facility': {
                'id': facility['id'],
                'name': facility['name'],
                'sapphire_managed': bool(facility['sapphire_managed']),
                'management_company': facility['management_company']
            }
        })
        
    except Exception as e:
        error_handler.log_error("Get Facility Management API Error", str(e))
        return jsonify({'success': False, 'message': f'Error retrieving facility: {str(e)}'}), 500

@api_routes.route('/facilities/<int:facility_id>/management', methods=['PUT'])
def update_facility_management(facility_id):
    """Update management information for a facility"""
    try:
        data = request.get_json()
        sapphire_managed = data.get('sapphire_managed', False)
        management_company = data.get('management_company', '').strip() or None
        
        conn = sqlite3.connect(db_config.inspection_db_path)
        cursor = conn.cursor()
        
        # Verify facility exists
        cursor.execute("SELECT id FROM facilities WHERE id = ?", (facility_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Facility not found'}), 404
        
        # Update management information
        cursor.execute("""
            UPDATE facilities 
            SET sapphire_managed = ?, management_company = ?
            WHERE id = ?
        """, (sapphire_managed, management_company, facility_id))
        
        conn.commit()
        conn.close()
        
        error_handler.log_info("Facility Management Updated", f"Updated facility {facility_id}", {
            'facility_id': facility_id,
            'sapphire_managed': sapphire_managed,
            'management_company': management_company
        })
        
        return jsonify({
            'success': True, 
            'message': 'Management information updated successfully'
        })
        
    except Exception as e:
        error_handler.log_error("Update Facility Management API Error", str(e))
        return jsonify({'success': False, 'message': f'Error updating facility: {str(e)}'}), 500

@api_routes.route('/management-companies', methods=['GET'])
def get_management_companies():
    """Get list of all existing management companies"""
    try:
        conn = sqlite3.connect(db_config.inspection_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT management_company
            FROM facilities 
            WHERE management_company IS NOT NULL 
            AND management_company != ''
            ORDER BY management_company
        """)
        
        companies = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return jsonify({
            'success': True,
            'companies': companies
        })
        
    except Exception as e:
        error_handler.log_error("Get Management Companies API Error", str(e))
        return jsonify({'success': False, 'message': f'Error retrieving companies: {str(e)}'}), 500
