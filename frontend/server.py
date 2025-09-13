#!/usr/bin/env python3
"""
Simple HTTP server to serve CardioGenie frontend
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 3001

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    # Change to frontend directory
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    # Start server
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"""
🚀 CardioGenie Frontend Server Started!

📱 Frontend URL: http://localhost:{PORT}
🏥 Open in browser: http://localhost:{PORT}/index.html

🔧 Backend should be running on: http://localhost:8000
💬 WebSocket endpoint: ws://localhost:8000/ws/chat

✅ Ready for Hackathon Demo!
        """)
        
        try:
            # Try to open browser automatically
            webbrowser.open(f'http://localhost:{PORT}/index.html')
        except:
            pass
            
        print("Serving CardioGenie Frontend... Press Ctrl+C to stop.")
        httpd.serve_forever()

if __name__ == "__main__":
    main() 