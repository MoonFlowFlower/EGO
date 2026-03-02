#!/usr/bin/env python3
"""
Mock emotiond service for integration testing.
Provides HTTP endpoints that mimic the real emotiond service behavior.
"""

import json
import time
import uuid
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading
import sys
import signal

class MockEmotiondHandler(BaseHTTPRequestHandler):
    """Mock HTTP handler for emotiond service endpoints."""
    
    def log_message(self, format, *args):
        """Suppress default logging for cleaner test output."""
        pass
    
    def do_POST(self):
        """Handle POST requests to emotiond endpoints."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8')) if post_data else {}
        except json.JSONDecodeError:
            data = {}
        
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        # Route to appropriate handler
        if path == '/api/v1/events':
            self._handle_events(data)
        elif path == '/api/v1/outcomes':
            self._handle_outcomes(data)
        elif path == '/api/v1/tools/result':
            self._handle_tool_result(data)
        else:
            self._send_error(404, f"Endpoint not found: {path}")
    
    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/health':
            self._handle_health()
        elif path == '/api/v1/status':
            self._handle_status()
        else:
            self._send_error(404, f"Endpoint not found: {path}")
    
    def _handle_events(self, data):
        """Handle user message events."""
        # Mock successful event processing
        response = {
            "event_id": str(uuid.uuid4()),
            "status": "processed",
            "timestamp": datetime.utcnow().isoformat(),
            "type": data.get("type", "user_message"),
            "learning_record_id": str(uuid.uuid4()) if data.get("type") == "user_message" else None
        }
        
        self._send_json_response(200, response)
    
    def _handle_outcomes(self, data):
        """Handle outcome events."""
        # Mock successful outcome processing
        response = {
            "outcome_id": str(uuid.uuid4()),
            "status": "recorded",
            "timestamp": datetime.utcnow().isoformat(),
            "outcome_type": data.get("outcome_type", "unknown"),
            "trace_id": data.get("trace_id", str(uuid.uuid4()))
        }
        
        self._send_json_response(200, response)
    
    def _handle_tool_result(self, data):
        """Handle tool result events."""
        # Mock tool result processing with status simulation
        status = data.get("status", "success")
        
        # Simulate different processing times based on status
        if status == "timeout":
            time.sleep(0.1)  # Brief delay to simulate timeout
        elif status == "failure":
            time.sleep(0.05)  # Brief delay to simulate processing
        
        response = {
            "result_id": str(uuid.uuid4()),
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "tool_name": data.get("tool_name", "unknown"),
            "payload_size": len(json.dumps(data).encode('utf-8')),
            "payload_size_valid": len(json.dumps(data).encode('utf-8')) <= 3072,  # 3KB limit
            "trace_pointer": f"trace://{uuid.uuid4()}"
        }
        
        self._send_json_response(200, response)
    
    def _handle_health(self):
        """Health check endpoint."""
        self._send_json_response(200, {"status": "healthy", "timestamp": datetime.utcnow().isoformat()})
    
    def _handle_status(self):
        """Status endpoint."""
        self._send_json_response(200, {
            "service": "emotiond-mock",
            "version": "mock-1.0.0",
            "status": "running",
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def _send_json_response(self, status_code, data):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = json.dumps(data, indent=2)
        self.wfile.write(response.encode('utf-8'))
    
    def _send_error(self, status_code, message):
        """Send error response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        error_response = json.dumps({
            "error": message,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat()
        })
        self.wfile.write(error_response.encode('utf-8'))

class MockEmotiondServer:
    """Mock emotiond server that can be started/stopped for testing."""
    
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
    
    def start(self):
        """Start the mock server."""
        self.server = HTTPServer((self.host, self.port), MockEmotiondHandler)
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True
        self.server_thread.start()
        print(f"Mock emotiond server started at http://{self.host}:{self.port}")
    
    def stop(self):
        """Stop the mock server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            if self.server_thread:
                self.server_thread.join(timeout=1)
            print("Mock emotiond server stopped")
    
    def is_running(self):
        """Check if server is running."""
        return self.server is not None and self.server_thread.is_alive()

def main():
    """Main entry point for running mock server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Mock emotiond service for testing')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8765, help='Port to bind to')
    parser.add_argument('--daemon', action='store_true', help='Run in daemon mode')
    
    args = parser.parse_args()
    
    server = MockEmotiondServer(args.host, args.port)
    
    def signal_handler(signum, frame):
        print("\nShutting down mock emotiond server...")
        server.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    server.start()
    
    if args.daemon:
        print("Mock emotiond server running in daemon mode")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    else:
        print("Mock emotiond server running. Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
    
    server.stop()

if __name__ == '__main__':
    main()