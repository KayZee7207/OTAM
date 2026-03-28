from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import os
import sys
import json
import threading
import webbrowser
import mimetypes
from otam.web.templates.home import build_home
from otam.web.templates.replay import build_replay_view
from otam.core.analysis import analyze_chat_logs
from otam.core.replays import readReplay
from otam.core import state

# Configuration
PORT = 7272
ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../assets'))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Parse URL
            parsed_path = urllib.parse.urlparse(self.path)
            path = parsed_path.path
            query = urllib.parse.parse_qs(parsed_path.query)
            
            # 1. Static Assets
            if path.startswith('/assets/'):
                self.serve_static(path)
                return

            # 2. View Replay/Directory
            if path.startswith('/view/'):
                decoded_path = urllib.parse.unquote(path[6:]) # strip /view/
                self.serve_view(decoded_path)
                return

            # 3. Root -> Home
            if path == '/':
                self.serve_view(os.getcwd())
                return
                
            self.send_error(404, "File not found")
            
        except Exception as e:
            self.send_error(500, str(e))
            traceback.print_exc()

    def do_POST(self):
        try:
            length = int(self.headers.get('content-length', 0))
            body = self.rfile.read(length)
            payload = json.loads(body)
            
            if self.path == '/analyzeReplay':
                self.handle_analyze(payload)
            elif self.path == '/runReplay':
                self.handle_run(payload)
            else:
                self.send_error(404, "Endpoint not found")
                
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())

    def serve_static(self, path):
        # path is like /assets/style.css
        filename = os.path.basename(path)
        file_path = os.path.join(ASSETS_DIR, filename)
        
        if os.path.exists(file_path):
            mime, _ = mimetypes.guess_type(file_path)
            self.send_response(200)
            self.send_header('Content-type', mime or 'application/octet-stream')
            self.end_headers()
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "Asset not found")

    def serve_view(self, path):
        # Determine if file or directory
        if os.path.isfile(path):
            if path.endswith('.sdfz'):
                content = build_replay_view(path)
            else:
                content = "File viewing not supported for this type."
        elif os.path.isdir(path):
            content = build_home(path)
        else:
            self.send_error(404, "Path not found")
            return
            
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))

    def handle_analyze(self, payload):
        filename = payload.get('filename')
        if not filename or not os.path.exists(filename):
            raise FileNotFoundError("Replay file not found")
        
        # 1. Parse Replay
        replay_data = readReplay(filename, chunks=True)
        
        # 2. Extract Chat
        chat_lines = []
        for _, chunk in replay_data.chunks:
            if chunk and chunk[0] == 7: # Chat message
                try:
                    # from, to, msg
                    msg_from = chunk[2]
                    msg_content = chunk[4:-1].decode('utf-8', errors='ignore')
                    
                    # Get sender name
                    sender_name = "Unknown"
                    for player in replay_data.setupScript['game'].get('player', []):
                         # Note: mapping logic is approximate, better to use the robust summary logic but this is quick for analysis
                         # The player ID in chunk[2] maps to the player index in the player list
                         if player.get('team') is not None: # Not spectator
                             pass 
                    
                    # Actually, let's use the robust logic we built in summary.py
                    # Refactoring: we should call process_replay to get the summary, then analyze that
                    pass
                except: continue

        # Reuse summary logic to get clean chat
        from otam.core.summary import process_replay
        summary = process_replay(replay_data)
        
        # Extract chat objects for AI
        # analyze_chat_logs expects list of (timestamp, player_name, msg_content)
        #chat_lines = []
        #for line in summary.logLines:
            # (time, from, to, type, content)
            #if line[3] == "MSG":
                #sender = summary.players[line[1]].name if line[1] in summary.players else "Unknown"
                #chat_lines.append((line[0], sender, line[4]))
        
        # 3. Call AI
        #from otam.core.analysis import analyze_chat_logs
        #result = analyze_chat_logs(chat_lines)
        
        # 4. Save State
        state.save_analysis(os.path.basename(filename), result)
        
        # 5. Respond
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "success", "data": result}).encode())

    def handle_run(self, payload):
        filename = payload.get('filename')
        os.startfile(filename) # Windows only
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"status": "success", "message": "Replay launched"}).encode())

import traceback

def run_server(url=None):
    server = HTTPServer(('', PORT), Handler)
    print(f"Server started at http://localhost:{PORT}")
    
    if url:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
        
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()
