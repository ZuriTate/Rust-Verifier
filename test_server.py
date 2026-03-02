import http.server
import socketserver

HOST = "127.0.0.1"
PORT = 8082

class TestHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            html = """<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body><h1>Test Page</h1></body>
</html>""".encode('utf-8')
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            self.wfile.flush()
        else:
            self.send_error(404)

if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer((HOST, PORT), TestHandler)
    print(f"Test server running on: http://{HOST}:{PORT}")
    server.serve_forever()
