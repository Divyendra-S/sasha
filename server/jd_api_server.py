"""
Simple HTTP API server for Job Description data.

This server provides REST endpoints to access the current state of JD data
extraction. It runs alongside the main bot and shares the same JD data instance.
"""

import json
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from threading import Thread
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class JDAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for JD API endpoints."""
    
    def __init__(self, jd_data_instance, *args, **kwargs):
        self.jd_data = jd_data_instance
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/api/jd-data':
            self.send_cors_headers()
            self.handle_jd_data_request()
        elif parsed_path.path == '/api/jd-status':
            self.send_cors_headers()
            self.handle_jd_status_request()
        elif parsed_path.path == '/api/health':
            self.send_cors_headers()
            self.handle_health_request()
        else:
            self.send_error(404, "Endpoint not found")
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS preflight."""
        self.send_cors_headers()
        self.end_headers()
    
    def send_cors_headers(self):
        """Send CORS headers to allow frontend access."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Type', 'application/json')
    
    def handle_jd_data_request(self):
        """Handle /api/jd-data requests."""
        logger.info("[JD_API] 🔄 JD data request received from frontend")
        try:
            if self.jd_data:
                # Get data in frontend format
                frontend_data = self.jd_data.to_frontend_format()
                logger.info(f"[JD_API] 📊 Sending data: title='{frontend_data.get('title')}', company='{frontend_data.get('company')}', extractedFields={list(self.jd_data._collected_fields)}")
                response = {
                    "success": True,
                    "data": frontend_data,
                    "extractedFields": list(self.jd_data._collected_fields),
                    "missingFields": self.jd_data.get_missing_fields(),
                    "isComplete": self.jd_data.is_complete(),
                    **self.jd_data.get_extraction_info()  # Include extraction status
                }
                
                # Mark extraction as consumed since frontend is fetching the data
                if self.jd_data.has_new_extraction():
                    logger.info(f"[JD_API] 🔄 Frontend consuming extraction data, clearing flag")
                    self.jd_data.mark_extraction_consumed()
            else:
                response = {
                    "success": False,
                    "error": "JD data not available",
                    "data": {
                        "title": "",
                        "company": "",
                        "description": "",
                        "requirements": [],
                        "benefits": [],
                        "location": "",
                        "salaryRange": "",
                        "employmentType": "Full-time"
                    }
                }
            
            self.end_headers()
            response_json = json.dumps(response, indent=2)
            logger.info(f"[JD_API] ✅ Sent response: {len(response_json)} bytes")
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"[JD_API] Error handling JD data request: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def handle_jd_status_request(self):
        """Handle /api/jd-status requests for extraction status only."""
        try:
            if self.jd_data:
                status_info = self.jd_data.get_extraction_info()
                response = {
                    "success": True,
                    **status_info
                }
                logger.info(f"[JD_API] 🔍 Status check: hasNewExtraction={status_info.get('hasNewExtraction', False)}, counter={status_info.get('extractionCounter', 0)}")
            else:
                response = {
                    "success": False,
                    "hasNewExtraction": False,
                    "error": "JD data not available"
                }
            
            self.end_headers()
            response_json = json.dumps(response)
            logger.info(f"[JD_API] ✅ Sending status response: {response_json}")
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            logger.error(f"[JD_API] Error handling status request: {e}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def handle_health_request(self):
        """Handle /api/health requests."""
        response = {
            "success": True,
            "status": "healthy",
            "message": "JD API server is running"
        }
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(f"[JD_API] {format % args}")


class JDAPIServer:
    """Simple HTTP server for JD API endpoints."""
    
    def __init__(self, jd_data_instance, port: int = 7861):
        self.jd_data = jd_data_instance
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.thread: Optional[Thread] = None
    
    def start(self):
        """Start the API server in a separate thread."""
        def handler_factory(*args, **kwargs):
            return JDAPIHandler(self.jd_data, *args, **kwargs)
        
        try:
            self.server = HTTPServer(('0.0.0.0', self.port), handler_factory)
            
            def run_server():
                logger.info(f"[JD_API] Starting JD API server on port {self.port}")
                logger.info(f"[JD_API] JD data endpoints available at:")
                logger.info(f"[JD_API]   • http://localhost:{self.port}/api/jd-data")
                logger.info(f"[JD_API]   • http://localhost:{self.port}/api/health")
                self.server.serve_forever()
            
            self.thread = Thread(target=run_server, daemon=True)
            self.thread.start()
            logger.info(f"[JD_API] JD API server started on port {self.port}")
            
        except Exception as e:
            logger.error(f"[JD_API] Failed to start API server: {e}")
    
    def stop(self):
        """Stop the API server."""
        if self.server:
            logger.info("[JD_API] Stopping JD API server...")
            self.server.shutdown()
            self.server.server_close()
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)
            logger.info("[JD_API] JD API server stopped")