#!/usr/bin/env python3
"""
Mock emotiond service for integration testing.
Simplified version focused on reliability.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import uuid
from datetime import datetime
import threading
import time

class MockEmotiondHandler(BaseHTTPRequestHandler):
    """Mock handler for emotiond HTTP endpoints."""
    
    # Class-level storage for persistence across requests
    storage = {
        'events': [],
        'predictions': {},
        'deltas': {}
    }
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/health':
            self._send_json({'status': 'ok', 'mock': True})
        elif self.path == '/events':
            self._send_json({'events': self.storage['events']})
        elif self.path.startswith('/predictions/'):
            prediction_id = self.path.split('/')[-1]
            prediction = self.storage['predictions'].get(prediction_id)
            if prediction:
                self._send_json(prediction)
            else:
                self._send_error(404, 'Prediction not found')
        elif self.path.startswith('/deltas/'):
            delta_id = self.path.split('/')[-1]
            delta = self.storage['deltas'].get(delta_id)
            if delta:
                self._send_json(delta)
            else:
                self._send_error(404, 'Delta not found')
        else:
            self._send_error(404, 'Not found')
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/event':
            self._handle_event()
        elif self.path == '/predict':
            self._handle_predict()
        else:
            self._send_error(404, 'Not found')
    
    def _handle_event(self):
        """Handle event submission."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_error(400, 'Empty request body')
                return
                
            post_data = self.rfile.read(content_length)
            event = json.loads(post_data.decode('utf-8'))
            
            # Add metadata
            event['id'] = str(uuid.uuid4())
            event['timestamp'] = datetime.utcnow().isoformat()
            event['mock'] = True
            
            # Store event
            self.storage['events'].append(event)
            
            # Generate mock response
            response = {'id': event['id'], 'status': 'accepted'}
            
            # For user_message events, generate mock prediction
            if event.get('meta', {}).get('subtype') == 'user_message':
                prediction_id = str(uuid.uuid4())
                prediction = {
                    'id': prediction_id,
                    'event_id': event['id'],
                    'predicted_delta': {
                        'valence': 0.1,
                        'arousal': 0.2,
                        'certainty': 0.8
                    },
                    'confidence': 0.85,
                    'model': 'mock-model-v1',
                    'timestamp': datetime.utcnow().isoformat(),
                    'mock': True
                }
                self.storage['predictions'][prediction_id] = prediction
                response['prediction_id'] = prediction_id
            
            # For outcome events, generate mock delta
            if event.get('type') == 'outcome':
                delta_id = str(uuid.uuid4())
                delta = {
                    'id': delta_id,
                    'event_id': event['id'],
                    'valence': event.get('valence', 0.0),
                    'arousal': event.get('arousal', 0.0),
                    'timestamp': datetime.utcnow().isoformat(),
                    'mock': True
                }
                self.storage['deltas'][delta_id] = delta
                response['delta_id'] = delta_id
            
            self._send_json(response, status=201)
            
        except json.JSONDecodeError:
            self._send_error(400, 'Invalid JSON')
        except Exception as e:
            self._send_error(500, f'Internal error: {str(e)}')
    
    def _handle_predict(self):
        """Handle prediction requests."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_error(400, 'Empty request body')
                return
                
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            prediction_id = str(uuid.uuid4())
            prediction = {
                'id': prediction_id,
                'predicted_delta': {
                    'valence': 0.1,
                    'arousal': 0.2,
                    'certainty': 0.8
                },
                'confidence': 0.85,
                'model': 'mock-model-v1',
                'timestamp': datetime.utcnow().isoformat(),
                'mock': True
            }
            
            self.storage['predictions'][prediction_id] = prediction
            self._send_json(prediction, status=201)
            
        except json.JSONDecodeError:
            self._send_error(400, 'Invalid JSON')
        except Exception as e:
            self._send_error(500, f'Internal error: {str(e)}')
    
    def _send_json(self, data, status=200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = json.dumps(data)
        self.wfile.write(response.encode('utf-8'))
    
    def _send_error(self, code, message):
        """Send error response."""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        error = {'error': message, 'mock': True}
        response = json.dumps(error)
        self.wfile.write(response.encode('utf-8'))

def start_mock_server(port=18080, host='127.0.0.1'):
    """Start the mock emotiond server in background thread."""
    server_address = (host, port)
    httpd = HTTPServer(server_address, MockEmotiondHandler)
    
    # Run in background thread
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    
    # Give server time to start
    time.sleep(0.5)
    
    return httpd, server_thread

if __name__ == '__main__':
    # Start server directly
    httpd, thread = start_mock_server()
    print(f"Mock emotiond service running on http://127.0.0.1:18080")
    print("Press Ctrl+C to stop")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        httpd.shutdown()