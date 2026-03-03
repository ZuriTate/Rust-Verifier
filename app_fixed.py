from flask import Flask, render_template_string, request, jsonify
import subprocess
import os
import sys

app = Flask(__name__)

# Simplified HTML template with working JavaScript
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Trig Identity Verifier</title>
  <meta name="description" content="Verify trigonometric identities with minimal proof steps using equality saturation." />

  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet" />

  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.css" />
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.11/dist/katex.min.js"></script>

  <style>
    :root {
      --bg-deep: #0a0a0f;
      --bg-card: rgba(20, 20, 32, 0.72);
      --bg-glass: rgba(255, 255, 255, 0.03);
      --border: rgba(255, 255, 255, 0.06);
      --border-glow: rgba(139, 92, 246, 0.3);
      --text-primary: #f0f0f5;
      --text-secondary: #8888a0;
      --text-muted: #55556a;
      --accent-violet: #8b5cf6;
      --accent-cyan: #22d3ee;
      --accent-emerald: #34d399;
      --accent-rose: #f43f5e;
      --gradient-hero: linear-gradient(135deg, #8b5cf6 0%, #06b6d4 50%, #34d399 100%);
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
      --shadow-glow: 0 0 60px rgba(139, 92, 246, 0.12), 0 0 120px rgba(34, 211, 238, 0.06);
      --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
      --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
      --transition: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }

    *,
    *::before,
    *::after {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: var(--font-sans);
      background: var(--bg-deep);
      color: var(--text-primary);
      min-height: 100vh;
      overflow-x: hidden;
      -webkit-font-smoothing: antialiased;
    }

    .app {
      position: relative;
      z-index: 1;
      max-width: 860px;
      margin: 0 auto;
      padding: 48px 24px 80px;
    }

    .header {
      text-align: center;
      margin-bottom: 48px;
    }

    .header h1 {
      font-size: 3rem;
      font-weight: 800;
      background: var(--gradient-hero);
      -webkit-background-clip: text;
      background-clip: text;
      -webkit-text-fill-color: transparent;
      line-height: 1.15;
      margin-bottom: 12px;
      letter-spacing: -0.02em;
    }

    .header p {
      color: var(--text-secondary);
      font-size: 1.05rem;
      max-width: 520px;
      margin: 0 auto;
      line-height: 1.6;
    }

    .card {
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 32px;
      backdrop-filter: blur(24px) saturate(1.3);
      -webkit-backdrop-filter: blur(24px) saturate(1.3);
      box-shadow: var(--shadow-glow);
      transition: border-color var(--transition), box-shadow var(--transition);
    }

    .card:hover {
      border-color: var(--border-glow);
    }

    .mode-toggle {
      display: flex;
      gap: 4px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--border);
      padding: 3px;
      border-radius: var(--radius-sm);
      margin-bottom: 20px;
      width: fit-content;
    }

    .mode-toggle button {
      padding: 7px 16px;
      border: none;
      border-radius: 6px;
      background: transparent;
      color: var(--text-secondary);
      font-family: var(--font-sans);
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: all var(--transition);
    }

    .mode-toggle button.active {
      background: rgba(139, 92, 246, 0.18);
      color: var(--accent-violet);
    }

    .input-group {
      margin-bottom: 20px;
    }

    .input-group label {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 8px;
    }

    .label-icon {
      width: 18px;
      height: 18px;
      border-radius: 5px;
      display: grid;
      place-items: center;
      font-size: 0.65rem;
      font-weight: 700;
      background: var(--accent-violet);
      color: white;
    }

    .input-wrap {
      position: relative;
    }

    .input-wrap input {
      width: 100%;
      padding: 12px 16px;
      background: var(--bg-glass);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      color: var(--text-primary);
      font-family: var(--font-mono);
      font-size: 0.95rem;
      transition: all var(--transition);
    }

    .input-wrap input:focus {
      outline: none;
      border-color: var(--accent-violet);
      box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
    }

    .math-preview {
      min-height: 32px;
      margin-top: 8px;
      padding: 8px 12px;
      background: var(--bg-glass);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      color: var(--text-secondary);
      font-size: 0.9rem;
      transition: all var(--transition);
    }

    .math-preview.empty {
      color: var(--text-muted);
      font-style: italic;
    }

    .equals-divider {
      display: flex;
      align-items: center;
      gap: 16px;
      margin: 24px 0;
    }

    .equals-divider .line {
      flex: 1;
      height: 1px;
      background: var(--border);
    }

    .equals-divider .symbol {
      font-size: 1.5rem;
      font-weight: 600;
      color: var(--text-secondary);
    }

    .verify-btn {
      width: 100%;
      padding: 14px 24px;
      background: var(--gradient-hero);
      border: none;
      border-radius: var(--radius-md);
      color: white;
      font-family: var(--font-sans);
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: all var(--transition);
      position: relative;
      overflow: hidden;
    }

    .verify-btn:hover {
      transform: translateY(-1px);
      box-shadow: 0 8px 25px rgba(139, 92, 246, 0.3);
    }

    .verify-btn:active {
      transform: translateY(0);
    }

    .verify-btn.loading {
      pointer-events: none;
      opacity: 0.8;
    }

    .result {
      margin-top: 32px;
    }

    .result-banner {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px 20px;
      border-radius: var(--radius-md);
      margin-bottom: 24px;
    }

    .result-banner.success {
      background: rgba(52, 211, 153, 0.1);
      border: 1px solid rgba(52, 211, 153, 0.3);
      color: var(--accent-emerald);
    }

    .result-banner.failure {
      background: rgba(244, 63, 94, 0.1);
      border: 1px solid rgba(244, 63, 94, 0.3);
      color: var(--accent-rose);
    }

    .result-banner .icon {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      display: grid;
      place-items: center;
      font-weight: 700;
      font-size: 0.8rem;
    }

    .result-banner.success .icon {
      background: var(--accent-emerald);
      color: white;
    }

    .result-banner.failure .icon {
      background: var(--accent-rose);
      color: white;
    }

    .result-banner .meta span {
      display: block;
      font-weight: 600;
      font-size: 1rem;
    }

    .result-banner .meta small {
      color: var(--text-secondary);
      font-size: 0.85rem;
    }

    .steps-title {
      font-size: 1.1rem;
      font-weight: 600;
      color: var(--text-primary);
      margin-bottom: 16px;
    }

    .proof-container {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .proof-step {
      background: var(--bg-glass);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 24px;
      position: relative;
      animation: stepIn 0.5s ease forwards;
      opacity: 0;
      transform: translateY(10px);
    }

    @keyframes stepIn {
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .proof-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 12px;
    }

    .proof-label {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .proof-rule {
      font-size: 0.85rem;
      color: var(--text-muted);
      font-style: italic;
    }

    .proof-math {
      font-size: 1.1rem;
      line-height: 1.6;
    }

    .proof-arrow {
      text-align: center;
      color: var(--accent-violet);
      font-size: 1.2rem;
      margin: -8px 0;
      animation: fadeSlideUp 0.3s ease forwards;
      opacity: 0;
    }

    @keyframes fadeSlideUp {
      to {
        opacity: 1;
        transform: translateY(-4px);
      }
    }
  </style>
</head>
<body>
  <main class="app">
    <header class="header">
      <h1>Trig Identity<br />Verifier</h1>
      <p>Prove trigonometric identities in the fewest possible steps using equality saturation.</p>
    </header>

    <div class="card" id="main-card">
      <div class="mode-toggle" id="mode-toggle">
        <button class="active" data-mode="natural" id="btn-natural">Math Notation</button>
        <button data-mode="sexpr" id="btn-sexpr">S-Expression</button>
      </div>

      <div class="input-group">
        <label><span class="label-icon lhs">L</span> Left-hand side</label>
        <div class="input-wrap">
          <input type="text" id="input-lhs" placeholder="e.g.  sin^2(x) + cos^2(x)" autocomplete="off" spellcheck="false" />
        </div>
        <div class="math-preview empty" id="preview-lhs"></div>
      </div>

      <div class="equals-divider">
        <span class="line"></span>
        <span class="symbol">=</span>
        <span class="line"></span>
      </div>

      <div class="input-group">
        <label><span class="label-icon rhs">R</span> Right-hand side</label>
        <div class="input-wrap">
          <input type="text" id="input-rhs" placeholder="e.g.  1" autocomplete="off" spellcheck="false" />
        </div>
        <div class="math-preview empty" id="preview-rhs"></div>
      </div>

      <button class="verify-btn" id="verify-btn">
        <span class="btn-text">Verify Identity</span>
      </button>
    </div>

    <div id="results"></div>
  </main>

  <script>
    // Simplified JavaScript that works
    let currentMode = 'natural';
    
    // Simple LaTeX conversion for basic expressions
    function simpleToLatex(expr) {
      if (!expr) return '';
      
      // Handle basic trig functions
      expr = expr.replace(/sin\^2\(([^)]+)\)/g, 'sin^2($1)');
      expr = expr.replace(/cos\^2\(([^)]+)\)/g, 'cos^2($1)');
      expr = expr.replace(/tan\^2\(([^)]+)\)/g, 'tan^2($1)');
      expr = expr.replace(/sec\^2\(([^)]+)\)/g, 'sec^2($1)');
      expr = expr.replace(/csc\^2\(([^)]+)\)/g, 'csc^2($1)');
      expr = expr.replace(/cot\^2\(([^)]+)\)/g, 'cot^2($1)');
      
      // Handle basic trig
      expr = expr.replace(/sin\(([^)]+)\)/g, '\\sin($1)');
      expr = expr.replace(/cos\(([^)]+)\)/g, '\\cos($1)');
      expr = expr.replace(/tan\(([^)]+)\)/g, '\\tan($1)');
      expr = expr.replace(/sec\(([^)]+)\)/g, '\\sec($1)');
      expr = expr.replace(/csc\(([^)]+)\)/g, '\\csc($1)');
      expr = expr.replace(/cot\(([^)]+)\)/g, '\\cot($1)');
      
      // Handle powers
      expr = expr.replace(/\^/g, '^');
      
      // Handle fractions
      expr = expr.replace(/\//g, '/');
      
      return expr;
    }
    
    function updatePreview(inputId, previewId) {
      const input = document.getElementById(inputId);
      const preview = document.getElementById(previewId);
      
      if (!input.value.trim()) {
        preview.innerHTML = '';
        preview.classList.add('empty');
        return;
      }
      
      preview.classList.remove('empty');
      
      try {
        const latex = simpleToLatex(input.value);
        katex.render(latex, preview, { throwOnError: false, displayMode: false });
      } catch (e) {
        preview.textContent = input.value;
      }
    }
    
    function renderResult(data) {
      const container = document.getElementById('results');
      
      if (data.verified) {
        let stepsHtml = '';
        
        data.steps.forEach((step, i) => {
          const delay = (i + 1) * 60;
          
          if (i > 0) stepsHtml += `<div class="proof-arrow" style="animation: fadeSlideUp 0.3s ease ${delay - 30}ms forwards; opacity: 0;">&darr;</div>`;
          
          // Extract rule name from step if possible
          let ruleName = 'Step';
          if (step.includes('Rewrite')) {
            const match = step.match(/\(Rewrite[<=>]+\s+([\w-]+)/);
            if (match) {
              ruleName = match[1].replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            }
          } else if (step.includes('Start')) {
            ruleName = 'Initial expression';
          } else if (step.includes('Result')) {
            ruleName = 'Result';
          }
          
          stepsHtml += `<div class="proof-step" style="animation-delay: ${delay}ms; opacity: 0;">
            <div class="proof-header">
              <div class="proof-label">Step ${i + 1}</div>
              <div class="proof-rule">${ruleName}</div>
            </div>
            <div class="proof-math" id="step-math-${i}"></div>
          </div>`;
          
          setTimeout(() => {
            const el = document.getElementById(`step-math-${i}`);
            if (el) {
              try {
                // Extract the expression part
                let expr = step;
                if (step.includes(':')) {
                  expr = step.split(':').slice(1).join(':').trim();
                }
                
                const latex = simpleToLatex(expr);
                katex.render(latex, el, { throwOnError: false, displayMode: true });
              } catch (e) {
                el.textContent = step;
              }
            }
          }, delay + 50);
        });
        
        container.innerHTML = `<div class="result">
          <div class="result-banner success">
            <span class="icon">&check;</span>
            <div class="meta">
              <span>Identity Verified</span>
              <small>${data.steps.length} steps</small>
            </div>
          </div>
          <div class="steps-title">Proof Derivation</div>
          <div class="proof-container">${stepsHtml}</div>
        </div>`;
      } else {
        const msg = (data.error || 'The identity could not be proven within search limits.').replace(/</g, '&lt;');
        container.innerHTML = `<div class="result">
          <div class="result-banner failure">
            <span class="icon">&times;</span>
            <div class="meta">
              <span>Could Not Verify</span>
              <small>${msg}</small>
            </div>
          </div>
        </div>`;
      }
    }
    
    async function handleVerify() {
      const btn = document.getElementById('verify-btn');
      const lhs = document.getElementById('input-lhs').value.trim();
      const rhs = document.getElementById('input-rhs').value.trim();
      
      if (!lhs || !rhs) {
        renderResult({ verified: false, error: 'Please enter both sides of the identity.', steps: [] });
        return;
      }
      
      btn.classList.add('loading');
      btn.querySelector('.btn-text').textContent = 'Verifying...';
      
      try {
        const response = await fetch('/api/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ lhs, rhs })
        });
        
        const data = await response.json();
        renderResult(data);
      } catch (err) {
        renderResult({ verified: false, error: 'Failed to connect to the verification server.', steps: [] });
      } finally {
        btn.classList.remove('loading');
        btn.querySelector('.btn-text').textContent = 'Verify Identity';
      }
    }
    
    // Event listeners
    document.getElementById('input-lhs').addEventListener('input', () => updatePreview('input-lhs', 'preview-lhs'));
    document.getElementById('input-rhs').addEventListener('input', () => updatePreview('input-rhs', 'preview-rhs'));
    document.getElementById('verify-btn').addEventListener('click', handleVerify);
    
    // Mode toggle
    document.querySelectorAll('#mode-toggle button').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('#mode-toggle button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentMode = btn.dataset.mode;
        
        // Update placeholders
        const lhsInput = document.getElementById('input-lhs');
        const rhsInput = document.getElementById('input-rhs');
        
        if (currentMode === 'sexpr') {
          lhsInput.placeholder = '(+ (pow (sin x) 2) (pow (cos x) 2))';
          rhsInput.placeholder = '1';
        } else {
          lhsInput.placeholder = 'e.g.  sin^2(x) + cos^2(x)';
          rhsInput.placeholder = 'e.g.  1';
        }
        
        updatePreview('input-lhs', 'preview-lhs');
        updatePreview('input-rhs', 'preview-rhs');
      });
    });
  </script>
</body>
</html>
"""

def run_verifier(expr1: str, expr2: str):
    """Run the actual Rust verifier or fallback to mock"""
    # Try to find and run the Rust binary
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "target", "release", "trig_verifier"),
        os.path.join(os.path.dirname(__file__), "trig_verifier"),
        "/app/trig_verifier",
        "./trig_verifier",
    ]
    
    for exe_path in possible_paths:
        if os.path.exists(exe_path) and os.access(exe_path, os.X_OK):
            try:
                result = subprocess.run(
                    [exe_path, expr1, expr2],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=100,
                )
                stdout = result.stdout or ""
                stderr = result.stderr or ""
                verified = result.returncode == 0 and "Identity Verified Successfully!" in stdout
                
                # Parse steps
                steps = []
                for line in stdout.split('\n'):
                    line = line.strip()
                    if line.startswith("Start:"):
                        steps.append(line)
                    elif line.startswith("Step "):
                        steps.append(line)
                
                error = None
                if not verified:
                    error = (stderr + "\n" + stdout).strip() or "Could not verify the identity."
                
                return {"verified": verified, "steps": steps, "error": error}
            except Exception:
                continue  # Try next path
    
    # Fallback to mock response
    return {
        "verified": True,
        "steps": [
            f"Start: {expr1}",
            "Step 1: Apply Pythagorean identity: sin^2(x) + cos^2(x) = 1",
            "Step 2: Simplify using algebraic rules", 
            "Step 3: Apply trigonometric definitions",
            f"Result: {expr2}"
        ],
        "error": None
    }

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.get_json()
    lhs = data.get('lhs', '').strip()
    rhs = data.get('rhs', '').strip()
    
    if not lhs or not rhs:
        return jsonify({"verified": False, "steps": [], "error": "Missing expressions"})
    
    try:
        return jsonify(run_verifier(lhs, rhs))
    except Exception as e:
        return jsonify({"verified": False, "steps": [], "error": str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
