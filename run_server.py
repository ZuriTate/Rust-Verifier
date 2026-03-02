import sys
import traceback

try:
    from server import *
    import http.server
    
    print("Starting server...")
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 8081), TrigHandler)
    print("Server created successfully")
    server.serve_forever()
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
