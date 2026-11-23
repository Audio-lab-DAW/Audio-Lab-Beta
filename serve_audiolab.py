#!/usr/bin/env python3
# AudioLab Studio local launcher. Run:  python3 serve_audiolab.py   (from this repository folder)
import http.server, os, socketserver, webbrowser, threading
PORT = 8765
HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path in ('/', '/index.html'):
            self.path = '/index.html'
        return super().do_GET()
    def end_headers(self):
        # cross-origin isolation (shared memory) + output-device selection + MIDI/mic
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'credentialless')
        self.send_header('Permissions-Policy', 'speaker-selection=(self), microphone=(self), midi=(self)')
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()
    def log_message(self, *a): pass
socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('127.0.0.1', PORT), H) as srv:
    url = f'http://localhost:{PORT}/'
    print('AudioLab Studio is running at', url, ' (press Ctrl+C to stop)')
    threading.Timer(.6, lambda: webbrowser.get('open -a "Google Chrome" %s').open(url) if os.path.exists('/Applications/Google Chrome.app') else webbrowser.open(url)).start()
    srv.serve_forever()
