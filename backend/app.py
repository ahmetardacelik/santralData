#!/usr/bin/env python3
"""
EPIAS Backend API - Flask Application
"""

from flask import Flask, request, jsonify, send_file, session, send_from_directory, render_template_string
from flask_cors import CORS
import os
import json
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import threading
import uuid
from epias_extractor import EpiasExtractor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-change-this')

# Configure CORS to support credentials and specific origins
CORS(app, 
     origins=["http://localhost:3000", "http://127.0.0.1:3000"],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# Global variables for session management
active_sessions = {}
active_extractions = {}

def create_app():
    """Factory function to create Flask app"""
    
    # Create necessary directories
    os.makedirs('backend/logs', exist_ok=True)
    os.makedirs('backend/downloads', exist_ok=True)
    os.makedirs('backend/static', exist_ok=True)
    
    return app

@app.route('/')
def home():
    """Serve the main web application"""
    try:
        # Serve the frontend HTML file
        return send_from_directory('../frontend', 'index.html')
    except:
        # Fallback to API info if frontend not found
        return jsonify({
            'message': 'EPIAS Elektrik Verisi API',
            'version': '1.0.0',
            'endpoints': {
                'POST /api/auth': 'Authentication',
                'GET /api/plants': 'Power plant list',
                'POST /api/extract': 'Extract data',
                'GET /api/extract/status/<task_id>': 'Extract status',
                'GET /api/download/<filename>': 'Download file',
                'GET /api/health': 'Health check'
            },
            'frontend': 'Frontend not found - accessing API mode'
        })

# Serve frontend static files
@app.route('/styles.css')
def serve_css():
    return send_from_directory('../frontend', 'styles.css')

@app.route('/script.js')
def serve_js():
    return send_from_directory('../frontend', 'script.js')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/api')
def api_info():
    """API information page"""
    return jsonify({
        'message': 'EPIAS Elektrik Verisi API',
        'version': '1.0.0',
        'endpoints': {
            'POST /api/auth': 'Authentication',
            'GET /api/plants': 'Power plant list',
            'POST /api/extract': 'Extract data',
            'GET /api/extract/status/<task_id>': 'Extract status',
            'GET /api/download/<filename>': 'Download file',
            'GET /api/health': 'Health check'
        }
    })

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'active_sessions': len(active_sessions),
        'active_extractions': len(active_extractions)
    })

@app.route('/api/auth', methods=['POST'])
def authenticate():
    """EPIAS Authentication"""
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({
                'success': False,
                'message': 'Username ve password gerekli'
            }), 400
        
        username = data['username'].strip()
        password = data['password'].strip()
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username ve password boş olamaz'
            }), 400
        
        # Create EPIAS extractor instance
        extractor = EpiasExtractor(username, password)
        
        # Authenticate
        auth_result = extractor.authenticate()
        
        if auth_result['success']:
            # Create session
            session_id = str(uuid.uuid4())
            active_sessions[session_id] = {
                'extractor': extractor,
                'username': username,
                'created_at': datetime.now(),
                'last_activity': datetime.now()
            }
            
            # Store session ID in Flask session
            session['session_id'] = session_id
            
            return jsonify({
                'success': True,
                'message': auth_result['message'],
                'session_id': session_id,
                'username': username
            })
        else:
            return jsonify(auth_result), 401
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Authentication error: {str(e)}'
        }), 500

@app.route('/api/plants', methods=['GET'])
def get_power_plants():
    """Get power plant list"""
    try:
        session_id = session.get('session_id')
        
        if not session_id or session_id not in active_sessions:
            return jsonify({
                'success': False,
                'message': 'Authentication gerekli'
            }), 401
        
        # Update last activity
        active_sessions[session_id]['last_activity'] = datetime.now()
        
        extractor = active_sessions[session_id]['extractor']
        plants_result = extractor.get_power_plant_list()
        
        return jsonify(plants_result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Power plants error: {str(e)}'
        }), 500

@app.route('/api/extract', methods=['POST'])
def extract_data():
    """Start data extraction"""
    try:
        session_id = session.get('session_id')
        
        if not session_id or session_id not in active_sessions:
            return jsonify({
                'success': False,
                'message': 'Authentication gerekli'
            }), 401
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'Request data gerekli'
            }), 400
        
        # Validate required fields
        required_fields = ['start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'message': f'{field} gerekli'
                }), 400
        
        start_date = data['start_date']
        end_date = data['end_date']
        power_plant_id = data.get('power_plant_id')
        chunk_days = data.get('chunk_days', 15)  # Default chunk size
        
        # Validate dates
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Geçersiz tarih formatı. YYYY-MM-DD kullanın'
            }), 400
        
        # Update last activity
        active_sessions[session_id]['last_activity'] = datetime.now()
        
        # Create task ID
        task_id = str(uuid.uuid4())
        
        # Start background extraction
        extractor = active_sessions[session_id]['extractor']
        
        def extraction_worker():
            try:
                # Update status
                active_extractions[task_id] = {
                    'status': 'running',
                    'progress': 0,
                    'message': 'Veri çekme başlatılıyor...',
                    'started_at': datetime.now(),
                    'current_period': None,
                    'data': None,
                    'error': None
                }
                
                def progress_callback(progress, current_start, current_end):
                    active_extractions[task_id].update({
                        'progress': progress,
                        'message': f'İşleniyor: {current_start} - {current_end}',
                        'current_period': {'start': current_start, 'end': current_end}
                    })
                
                # Extract data
                result = extractor.get_data_for_period(
                    start_date, 
                    end_date, 
                    chunk_days=chunk_days,
                    power_plant_id=power_plant_id,
                    progress_callback=progress_callback
                )
                
                if result['success']:
                    # Generate Excel file
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"epias_data_{timestamp}.xlsx"
                    
                    excel_result = extractor.save_to_excel(
                        result['data'], 
                        filename=filename,
                        include_power_plants=True
                    )
                    
                    if excel_result['success']:
                        active_extractions[task_id].update({
                            'status': 'completed',
                            'progress': 100,
                            'message': f'Tamamlandı! {result["count"]} kayıt işlendi',
                            'completed_at': datetime.now(),
                            'data': {
                                'record_count': result['count'],
                                'period': result['period'],
                                'file_info': {
                                    'filename': excel_result['filename'],
                                    'file_size_mb': excel_result['file_size_mb'],
                                    'download_url': f'/api/download/{excel_result["filename"]}'
                                }
                            }
                        })
                    else:
                        active_extractions[task_id].update({
                            'status': 'error',
                            'message': f'Excel oluşturma hatası: {excel_result["message"]}',
                            'error': excel_result['message']
                        })
                else:
                    active_extractions[task_id].update({
                        'status': 'error',
                        'message': f'Veri çekme hatası: {result["message"]}',
                        'error': result['message']
                    })
                    
            except Exception as e:
                active_extractions[task_id].update({
                    'status': 'error',
                    'message': f'İşlem hatası: {str(e)}',
                    'error': str(e)
                })
        
        # Start extraction in background
        thread = threading.Thread(target=extraction_worker)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Veri çekme işlemi başlatıldı',
            'task_id': task_id,
            'status_url': f'/api/extract/status/{task_id}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Extract error: {str(e)}'
        }), 500

@app.route('/api/extract/status/<task_id>', methods=['GET'])
def get_extraction_status(task_id):
    """Get extraction status"""
    try:
        if task_id not in active_extractions:
            return jsonify({
                'success': False,
                'message': 'Task bulunamadı'
            }), 404
        
        task_info = active_extractions[task_id].copy()
        
        # Convert datetime objects to strings
        if 'started_at' in task_info:
            task_info['started_at'] = task_info['started_at'].isoformat()
        if 'completed_at' in task_info:
            task_info['completed_at'] = task_info['completed_at'].isoformat()
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'task_info': task_info
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Status error: {str(e)}'
        }), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download generated Excel file"""
    try:
        # Security: Check filename
        if not filename.endswith('.xlsx'):
            return jsonify({
                'success': False,
                'message': 'Geçersiz dosya türü'
            }), 400
        
        # Security: Sanitize filename
        safe_filename = secure_filename(filename)
        
        # Use absolute path to prevent path resolution issues
        downloads_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', 'downloads')
        filepath = os.path.join(downloads_dir, safe_filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'message': f'Dosya bulunamadı: {filepath}'
            }), 404
        
        return send_file(
            filepath,
            as_attachment=True,
            download_name=safe_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Download error: {str(e)}'
        }), 500

@app.route('/api/sessions', methods=['GET'])
def get_session_info():
    """Get current session info"""
    try:
        session_id = session.get('session_id')
        
        if not session_id or session_id not in active_sessions:
            return jsonify({
                'authenticated': False,
                'message': 'No active session'
            })
        
        session_info = active_sessions[session_id]
        
        return jsonify({
            'authenticated': True,
            'session_id': session_id,
            'username': session_info['username'],
            'created_at': session_info['created_at'].isoformat(),
            'last_activity': session_info['last_activity'].isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Session error: {str(e)}'
        }), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout and cleanup session"""
    try:
        session_id = session.get('session_id')
        
        if session_id and session_id in active_sessions:
            del active_sessions[session_id]
        
        session.clear()
        
        return jsonify({
            'success': True,
            'message': 'Logout başarılı'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Logout error: {str(e)}'
        }), 500

# Session cleanup (remove old sessions)
def cleanup_old_sessions():
    """Clean up old inactive sessions"""
    current_time = datetime.now()
    expired_sessions = []
    
    for session_id, session_info in active_sessions.items():
        # Remove sessions older than 2 hours
        if (current_time - session_info['last_activity']).seconds > 7200:
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del active_sessions[session_id]

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Endpoint bulunamadı'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Sunucu hatası'
    }), 500

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"🚀 EPIAS Backend API starting on port {port}")
    print(f"🔗 Web Interface: http://localhost:{port}/")
    print(f"🔗 API Documentation: http://localhost:{port}/api")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 