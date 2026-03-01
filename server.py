import http.server
import subprocess
import urllib.parse
import os
import sys

PORT = 8081
HOST = "127.0.0.1"

class TrigHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        print(f"--> [GET] Browser requested: {self.path}")
        if self.path == '/':
            html = """<!DOCTYPE html>
            <html>
            <head><title>Trig Identity Verifier</title></head>
            <body style="font-family: Arial, sans-serif; padding: 2rem; max-width: 800px;">
                <h2>Trigonometric Identity Verifier (Shortest Path)</h2>
                <p>Enter expressions in Lisp-like prefix notation. Examples:</p>
                <ul>
                    <li><code>(+ (pow (sin x) 2) (pow (cos x) 2))</code> = sin²(x) + cos²(x)</li>
                    <li><code>(* (tan x) (cos x))</code> = tan(x)cos(x)</li>
                </ul>
                <form action="/verify" method="POST">
                    <label><b>Expression 1:</b></label><br>
                    <input type="text" name="expr1" style="width: 100%; padding: 8px;" value="(- (+ (pow (sec x) 2) (* 2 (tan x))) 1)"><br><br>
                    <label><b>Expression 2:</b></label><br>
                    <input type="text" name="expr2" style="width: 100%; padding: 8px;" value="(* (tan x) (+ (tan x) 2))"><br><br>
                    <input type="submit" value="Find Shortest Proof" style="padding: 10px 20px;">
                </form>
            </body>
            </html>
            """.encode('utf-8')
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(html)))
            self.end_headers()
            self.wfile.write(html)
            self.wfile.flush()
        elif self.path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
        else:
            self.send_error(404)

    def do_POST(self):
        print(f"-->[POST] Browser submitted form to: {self.path}")
        if self.path == '/verify':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(post_data)
            
            expr1 = params.get('expr1',[''])[0]
            expr2 = params.get('expr2', [''])[0]

            exe_ext = ".exe" if sys.platform == "win32" else ""
            exe_path = os.path.abspath(os.path.join(".", "target", "release", f"trig_verifier{exe_ext}"))

            if not os.path.exists(exe_path):
                output = f"Error: Executable not found at {exe_path}. Did you run 'cargo build --release'?"
            else:
                try:
                    print(f"--> Running Rust binary with: {expr1} and {expr2}")
                    # ADDED encoding="utf-8" HERE SO WINDOWS DOESN'T CRASH ON EMOJIS!
                    result = subprocess.run([exe_path, expr1, expr2],
                        capture_output=True,
                        text=True,
                        encoding="utf-8", 
                        timeout=100 # Bumped timeout slightly for harder math problems
                    )
                    output = result.stdout if result.returncode == 0 else result.stderr + result.stdout
                except subprocess.TimeoutExpired:
                    output = "❌ Error: The search timed out. The problem was too complex or requires more node limits in the Rust engine."
                except Exception as e:
                    output = str(e)

            res_html = f"""<!DOCTYPE html>
            <html>
            <body style="font-family: Arial, sans-serif; padding: 2rem; max-width: 800px;">
                <h2>Verification Result</h2>
                <pre style="background: #f4f4f4; padding: 1rem; border-radius: 5px; font-size: 16px; white-space: pre-wrap;">{output}</pre>
                <br>
                <a href="/" style="padding: 10px 20px; background: #eee; text-decoration: none; color: black; border-radius: 5px;">Try Another</a>
            </body>
            </html>
            """.encode('utf-8')
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(res_html)))
            self.end_headers()
            self.wfile.write(res_html)
            self.wfile.flush()

if __name__ == "__main__":
    server = http.server.ThreadingHTTPServer((HOST, PORT), TrigHandler)
    print(f"✅ Web server successfully running on: http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()