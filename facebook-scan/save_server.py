"""Tiny local sink: POST body to /<name> saves raw/<name>. Used by the Playwright scan code."""
import http.server, os, re
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'raw')
class H(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        name = re.sub(r'[^\w.-]', '_', self.path.strip('/'))
        body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
        open(os.path.join(RAW, name), 'wb').write(body)
        self.send_response(200); self.end_headers(); self.wfile.write(b'ok')
    def log_message(self, *a): pass
http.server.HTTPServer(('127.0.0.1', 8765), H).serve_forever()
