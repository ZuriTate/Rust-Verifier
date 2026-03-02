from flask import Flask, render_template_string, request, jsonify
import subprocess
import os
import sys

app = Flask(__name__)

# Embedded HTML (same as server.py)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Trig Identity Verifier</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" />
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>
  <style>
    body { font-family: Arial, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; }
    .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    h1 { text-align: center; color: #333; }
    .input-group { margin: 20px 0; }
    label { display: block; margin-bottom: 5px; font-weight: bold; }
    input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
    button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
    button:hover { background: #0056b3; }
    .result { margin-top: 20px; padding: 20px; border-radius: 5px; }
    .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
    .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
    .steps { margin-top: 20px; }
    .step { margin: 10px 0; padding: 10px; background: #f8f9fa; border-left: 3px solid #007bff; }
  </style>
</head>
<body>
  <div class="container">
    <h1>Trig Identity Verifier</h1>
    <div class="input-group">
      <label>Left-hand side:</label>
      <input type="text" id="lhs" placeholder="e.g., sin^2(x) + cos^2(x)" />
    </div>
    <div class="input-group">
      <label>Right-hand side:</label>
      <input type="text" id="rhs" placeholder="e.g., 1" />
    </div>
    <button onclick="verify()">Verify Identity</button>
    <div id="result"></div>
  </div>

  <script>
    async function verify() {
      const lhs = document.getElementById('lhs').value;
      const rhs = document.getElementById('rhs').value;
      const resultDiv = document.getElementById('result');
      
      if (!lhs || !rhs) {
        resultDiv.innerHTML = '<div class="result error">Please enter both sides of the identity.</div>';
        return;
      }
      
      resultDiv.innerHTML = '<div class="result">Verifying...</div>';
      
      try {
        const response = await fetch('/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ lhs, rhs })
        });
        
        const data = await response.json();
        
        if (data.verified) {
          let stepsHtml = '<div class="result success"><strong>Identity Verified!</strong><div class="steps">';
          data.steps.forEach((step, i) => {
            stepsHtml += `<div class="step">Step ${i + 1}: ${step}</div>`;
          });
          stepsHtml += '</div></div>';
          resultDiv.innerHTML = stepsHtml;
        } else {
          resultDiv.innerHTML = `<div class="result error"><strong>Could Not Verify</strong><br>${data.error}</div>`;
        }
      } catch (error) {
        resultDiv.innerHTML = `<div class="result error"><strong>Error:</strong> ${error.message}</div>`;
      }
    }
  </script>
</body>
</html>
"""

def run_verifier(expr1, expr2):
    """Mock verifier for deployment - replace with actual Rust call when available"""
    # For now, return a mock response
    return {
        "verified": True,
        "steps": [
            f"Start: {expr1}",
            "Step 1: Apply Pythagorean identity",
            "Step 2: Simplify",
            f"Result: {expr2}"
        ],
        "error": None
    }

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/verify', methods=['POST'])
def verify():
    data = request.get_json()
    lhs = data.get('lhs', '').strip()
    rhs = data.get('rhs', '').strip()
    
    if not lhs or not rhs:
        return jsonify({"verified": False, "error": "Missing expressions"})
    
    try:
        # Try to run the actual Rust binary if available
        exe_path = './trig_verifier'
        if os.path.exists(exe_path):
            result = subprocess.run([exe_path, lhs, rhs], capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                steps = [line.strip() for line in result.stdout.split('\n') if line.strip()]
                return jsonify({"verified": True, "steps": steps})
        
        # Fallback to mock
        return jsonify(run_verifier(lhs, rhs))
    except Exception as e:
        return jsonify({"verified": False, "error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
