import http.server
import subprocess
import urllib.parse
import os
import sys
import json

PORT = int(os.environ.get("PORT", 8081))
HOST = "0.0.0.0"  # Listen on all interfaces for cloud hosting

def _rust_exe_path():
    # Try different paths for the compiled binary
    possible_paths = [
        os.path.join(os.path.dirname(__file__), "target", "release", "trig_verifier"),
        os.path.join(os.path.dirname(__file__), "trig_verifier"),
        "/app/trig_verifier",  # Docker path
        "./trig_verifier",     # Current directory
    ]
    for path in possible_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path
    return os.path.join(os.path.dirname(__file__), "target", "release", "trig_verifier")

def _parse_steps(stdout: str):
    steps = []
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("Start"):
            parts = line.split(":", 1)
            if len(parts) == 2:
                steps.append(parts[1].strip())
        elif line.startswith("Step "):
            parts = line.split(":", 1)
            if len(parts) == 2:
                steps.append(parts[1].strip())
    return steps

def _run_verifier(expr1: str, expr2: str):
    exe_path = _rust_exe_path()

    if not os.path.exists(exe_path):
        output = f"Error: Executable not found at {exe_path}. Did you run 'cargo build --release'?"
        return {"verified": False, "steps": [], "error": output, "raw": output}

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
        raw = stdout if result.returncode == 0 else (stderr + stdout)
        verified = result.returncode == 0 and "Identity Verified Successfully!" in stdout
        steps = _parse_steps(stdout)
        error = None
        if not verified:
            error = (stderr + "\n" + stdout).strip() or "Could not verify the identity."
        return {"verified": verified, "steps": steps, "error": error, "raw": raw}
    except subprocess.TimeoutExpired:
        output = "Error: The search timed out. The problem was too complex or requires more node limits in the Rust engine."
        return {"verified": False, "steps": [], "error": output, "raw": output}
    except Exception as e:
        output = str(e)
        return {"verified": False, "steps": [], "error": output, "raw": output}

class TrigHandler(http.server.BaseHTTPRequestHandler):
    
    def do_GET(self):
        print(f"--> [GET] Browser requested: {self.path}")
        if self.path == '/':
            html = r"""<!DOCTYPE html>
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
      font-weight: 800;
      color: #fff;
    }

    .label-icon.lhs {
      background: var(--accent-violet);
    }

    .label-icon.rhs {
      background: var(--accent-cyan);
    }

    .input-wrap input {
      width: 100%;
      padding: 14px 18px;
      background: var(--bg-glass);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      color: var(--text-primary);
      font-family: var(--font-mono);
      font-size: 0.95rem;
      outline: none;
      transition: border-color var(--transition), box-shadow var(--transition);
    }

    .math-preview {
      min-height: 32px;
      margin-top: 8px;
      padding: 8px 12px;
      border-radius: var(--radius-sm);
      background: rgba(139, 92, 246, 0.04);
      border: 1px solid rgba(139, 92, 246, 0.08);
      display: flex;
      align-items: center;
      font-size: 1.1rem;
      color: var(--text-primary);
      transition: opacity var(--transition);
    }

    .math-preview.empty {
      opacity: 0.3;
    }

    .equals-divider {
      display: flex;
      align-items: center;
      gap: 16px;
      margin: 4px 0 20px;
      padding: 0 4px;
    }

    .equals-divider .line {
      flex: 1;
      height: 1px;
      background: linear-gradient(90deg, transparent, var(--border), transparent);
    }

    .equals-divider .symbol {
      font-size: 1.4rem;
      font-weight: 700;
      color: var(--accent-violet);
      text-shadow: 0 0 20px rgba(139, 92, 246, 0.4);
    }

    .verify-btn {
      width: 100%;
      padding: 16px;
      border: none;
      border-radius: var(--radius-md);
      background: var(--gradient-hero);
      color: #fff;
      font-family: var(--font-sans);
      font-size: 1rem;
      font-weight: 700;
      cursor: pointer;
      position: relative;
      overflow: hidden;
      transition: transform 0.15s ease, box-shadow var(--transition);
    }

    .verify-btn.loading {
      pointer-events: none;
    }

    .verify-btn .shimmer {
      position: absolute;
      inset: 0;
      background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.15) 50%, transparent 100%);
      transform: translateX(-100%);
    }

    .verify-btn.loading .shimmer {
      animation: shimmer 1.2s ease-in-out infinite;
    }

    @keyframes shimmer {
      100% {
        transform: translateX(100%);
      }
    }

    .result {
      margin-top: 32px;
      animation: fadeSlideUp 0.5s ease;
    }

    @keyframes fadeSlideUp {
      from {
        opacity: 0;
        transform: translateY(20px);
      }

      to {
        opacity: 1;
        transform: translateY(0);
      }
    }

    .result-banner {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 18px 22px;
      border-radius: var(--radius-md);
      margin-bottom: 24px;
      font-weight: 600;
      font-size: 1.05rem;
    }

    .result-banner.success {
      background: rgba(52, 211, 153, 0.08);
      border: 1px solid rgba(52, 211, 153, 0.2);
      color: var(--accent-emerald);
    }

    .result-banner.failure {
      background: rgba(244, 63, 94, 0.08);
      border: 1px solid rgba(244, 63, 94, 0.2);
      color: var(--accent-rose);
    }

    .steps-title {
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.06em;
      margin-bottom: 16px;
    }

    .proof-step {
      background: var(--bg-glass);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 24px;
      margin-bottom: 20px;
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
      margin-bottom: 16px;
      gap: 12px;
    }

    .proof-label {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--accent-cyan);
      text-transform: uppercase;
      letter-spacing: 0.1em;
      white-space: nowrap;
    }

    .proof-rule {
      font-size: 0.85rem;
      font-weight: 500;
      color: var(--text-secondary);
      font-style: italic;
      text-align: right;
      flex: 1;
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .proof-math {
      font-size: 1.4rem;
      text-align: center;
      padding: 20px;
      background: rgba(0, 0, 0, 0.2);
      border-radius: var(--radius-sm);
      color: var(--text-primary);
      overflow-x: auto;
    }

    .proof-arrow {
      display: flex;
      justify-content: center;
      margin-bottom: 20px;
      color: var(--accent-violet);
      font-size: 1.2rem;
      opacity: 0.6;
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

      <button class="verify-btn" id="verify-btn" onclick="handleVerify()">
        <span class="shimmer"></span>
        <span class="btn-text">Verify Identity</span>
      </button>

      <div id="results"></div>
    </div>
  </main>

  <script>
    let mode = 'natural';

    function tokenize(input) {
      const tokens = [];
      let i = 0;
      const s = input.replace(/\s+/g, ' ').trim();
      while (i < s.length) {
        if (s[i] === ' ') { i++; continue; }
        if ('()+*-/^'.includes(s[i])) { tokens.push({ type: 'op', value: s[i] }); i++; continue; }
        if (/[0-9]/.test(s[i])) {
          let num = '';
          while (i < s.length && /[0-9]/.test(s[i])) { num += s[i]; i++; }
          tokens.push({ type: 'num', value: num });
          continue;
        }
        if (/[a-zA-Z_]/.test(s[i])) {
          let id = '';
          while (i < s.length && /[a-zA-Z_0-9]/.test(s[i])) { id += s[i]; i++; }
          const funcs = ['sin', 'cos', 'tan', 'csc', 'sec', 'cot', 'neg'];
          tokens.push({ type: funcs.includes(id) ? 'func' : 'var', value: id });
          continue;
        }
        i++;
      }
      return tokens;
    }

    function parseExpr(tokens, pos) {
      let [left, p] = parseTerm(tokens, pos);
      while (p < tokens.length && tokens[p].type === 'op' && (tokens[p].value === '+' || tokens[p].value === '-')) {
        const op = tokens[p].value; p++;
        let [right, p2] = parseTerm(tokens, p);
        left = `(${op} ${left} ${right})`;
        p = p2;
      }
      return [left, p];
    }

    function parseTerm(tokens, pos) {
      let [left, p] = parsePower(tokens, pos);
      while (p < tokens.length && tokens[p].type === 'op' && (tokens[p].value === '*' || tokens[p].value === '/')) {
        const op = tokens[p].value; p++;
        let [right, p2] = parsePower(tokens, p);
        left = `(${op} ${left} ${right})`;
        p = p2;
      }
      return [left, p];
    }

    function parsePower(tokens, pos) {
      let [base, p] = parseUnary(tokens, pos);
      if (p < tokens.length && tokens[p].type === 'op' && tokens[p].value === '^') {
        p++;
        let [exp, p2] = parsePower(tokens, p);
        return [`(pow ${base} ${exp})`, p2];
      }
      return [base, p];
    }

    function parseUnary(tokens, pos) {
      if (pos >= tokens.length) return ['?', pos];

      if (tokens[pos].type === 'func') {
        const fname = tokens[pos].value;
        let p = pos + 1;
        if (p < tokens.length && tokens[p].type === 'op' && tokens[p].value === '^') {
          p++;
          if (p < tokens.length && tokens[p].type === 'num') {
            const exp = tokens[p].value; p++;
            let [arg, p2] = parseAtom(tokens, p);
            return [`(pow (${fname} ${arg}) ${exp})`, p2];
          }
        }
        let [arg, p2] = parseAtom(tokens, p);
        return [`(${fname} ${arg})`, p2];
      }

      if (tokens[pos].type === 'op' && tokens[pos].value === '-') {
        let [arg, p2] = parseUnary(tokens, pos + 1);
        return [`(neg ${arg})`, p2];
      }

      return parseAtom(tokens, pos);
    }

    function parseAtom(tokens, pos) {
      if (pos >= tokens.length) return ['?', pos];
      if (tokens[pos].type === 'num') return [tokens[pos].value, pos + 1];
      if (tokens[pos].type === 'var') return [tokens[pos].value, pos + 1];
      if (tokens[pos].type === 'op' && tokens[pos].value === '(') {
        let [expr, p] = parseExpr(tokens, pos + 1);
        if (p < tokens.length && tokens[p].value === ')') p++;
        return [expr, p];
      }
      if (tokens[pos].type === 'func') return parseUnary(tokens, pos);
      return ['?', pos + 1];
    }

    function naturalToSexpr(input) {
      if (!input.trim()) return '';
      try {
        const tokens = tokenize(input);
        if (tokens.length === 0) return '';
        const [result] = parseExpr(tokens, 0);
        return result;
      } catch { return ''; }
    }

    function getSexpr(inputId) {
      const raw = document.getElementById(inputId).value.trim();
      if (!raw) return '';
      return mode === 'sexpr' ? raw : naturalToSexpr(raw);
    }

    function tokenizeSexpr(s) {
      const toks = [];
      let i = 0;
      while (i < s.length) {
        if (s[i] === ' ' || s[i] === '\t') { i++; continue; }
        if (s[i] === '(' || s[i] === ')') { toks.push(s[i]); i++; continue; }
        let word = '';
        while (i < s.length && s[i] !== ' ' && s[i] !== '(' && s[i] !== ')') { word += s[i]; i++; }
        toks.push(word);
      }
      return toks;
    }

    function parseSexprAST(tokens, pos) {
      if (pos >= tokens.length) return [null, pos];
      if (tokens[pos] === '(') {
        pos++;
        const op = tokens[pos]; pos++;
        const children = [];
        while (pos < tokens.length && tokens[pos] !== ')') {
          const [child, newPos] = parseSexprAST(tokens, pos);
          children.push(child);
          pos = newPos;
        }
        pos++;
        return [{ type: 'call', op, children }, pos];
      }
      return [{ type: 'atom', value: tokens[pos] }, pos + 1];
    }

    function _isAtomValue(node, v) {
      return node && node.type === 'atom' && node.value === v;
    }

    function _nodeKey(node) {
      if (!node) return '';
      if (node.type === 'atom') return `A:${node.value}`;
      return `C:${node.op}(${node.children.map(_nodeKey).join(',')})`;
    }

    function _normalizeAST(node) {
      if (!node) return null;
      if (node.type === 'atom') return node;

      const op = node.op;
      const kids = (node.children || []).map(_normalizeAST).filter(x => x);

      if (op === 'Rewrite=>' || op === 'Rewrite<=' || op === 'Rewrite<=>') {
        return kids[1] || null;
      }

      if (op === 'neg') {
        const inner = kids[0];
        if (inner && inner.type === 'call' && inner.op === 'neg') return inner.children[0] || null;
        return { type: 'call', op: 'neg', children: [inner] };
      }

      if (op === '+') {
        let flat = [];
        for (const k of kids) {
          if (k && k.type === 'call' && k.op === '+') flat.push(...(k.children || []));
          else flat.push(k);
        }
        flat = flat.filter(k => !_isAtomValue(k, '0'));
        flat.sort((a, b) => _nodeKey(a).localeCompare(_nodeKey(b)));
        if (flat.length === 0) return { type: 'atom', value: '0' };
        if (flat.length === 1) return flat[0];
        return { type: 'call', op: '+', children: flat };
      }

      if (op === '*') {
        let flat = [];
        for (const k of kids) {
          if (k && k.type === 'call' && k.op === '*') flat.push(...(k.children || []));
          else flat.push(k);
        }
        if (flat.some(k => _isAtomValue(k, '0'))) return { type: 'atom', value: '0' };
        flat = flat.filter(k => !_isAtomValue(k, '1'));
        flat.sort((a, b) => _nodeKey(a).localeCompare(_nodeKey(b)));
        if (flat.length === 0) return { type: 'atom', value: '1' };
        if (flat.length === 1) return flat[0];
        return { type: 'call', op: '*', children: flat };
      }

      if (op === '-') {
        const a = kids[0];
        const b = kids[1];
        if (!b) return a;
        if (_isAtomValue(b, '0')) return a;
        if (_isAtomValue(a, '0')) return _normalizeAST({ type: 'call', op: 'neg', children: [b] });
        return { type: 'call', op: '-', children: [a, b] };
      }

      if (op === '/') {
        const a = kids[0];
        const b = kids[1];
        if (b && _isAtomValue(b, '1')) return a;
        return { type: 'call', op: '/', children: [a, b] };
      }

      if (op === 'pow') {
        const base = kids[0];
        const exp = kids[1];
        if (_isAtomValue(exp, '1')) return base;
        if (_isAtomValue(exp, '0')) return { type: 'atom', value: '1' };
        return { type: 'call', op: 'pow', children: [base, exp] };
      }

      return { type: 'call', op, children: kids };
    }

    function _astToCanonicalSexpr(node) {
      if (!node) return '';
      if (node.type === 'atom') return node.value;
      return `(${node.op} ${node.children.map(_astToCanonicalSexpr).join(' ')})`;
    }

    function canonicalizeSexpr(sexpr) {
      if (!sexpr) return '';
      try {
        const tokens = tokenizeSexpr(sexpr);
        const [ast] = parseSexprAST(tokens, 0);
        const normalized = _normalizeAST(ast);
        return _astToCanonicalSexpr(normalized);
      } catch {
        return sexpr;
      }
    }

    const PRECEDENCE = {
      '+': 10,
      '-': 10,
      '*': 20,
      '/': 20,
      'neg': 30,
      'pow': 40,
      'func': 50,
      'atom': 60,
    };

    function _needsParens(childNode, parentOp) {
      if (!childNode || childNode.type !== 'call') return false;
      const childPrec = PRECEDENCE[childNode.op] ?? PRECEDENCE.atom;
      const parentPrec = PRECEDENCE[parentOp] ?? PRECEDENCE.atom;
      return childPrec < parentPrec;
    }

    function astToLatex(node, parentOp = null) {
      if (!node) return '';
      if (node.type === 'atom') return node.value;
      const op = node.op;
      const c = node.children;

      if (op.startsWith('Rewrite')) return astToLatex(c[1], parentOp);

      const isTrig = ['sin', 'cos', 'tan', 'csc', 'sec', 'cot'].includes(op);
      if (isTrig) {
        return `\\${op}\\left(${astToLatex(c[0], 'func')}\\right)`;
      }

      if (op === 'neg') {
        const inner = astToLatex(c[0], 'neg');
        const latex = `-${inner}`;
        if (parentOp && PRECEDENCE.neg < (PRECEDENCE[parentOp] ?? PRECEDENCE.atom)) {
          return `\\left(${latex}\\right)`;
        }
        return latex;
      }

      if (op === '+') {
        const left = astToLatex(c[0], '+');
        const right = astToLatex(c[1], '+');
        const latex = `${left} + ${right}`;
        if (parentOp && PRECEDENCE['+'] < (PRECEDENCE[parentOp] ?? PRECEDENCE.atom)) {
          return `\\left(${latex}\\right)`;
        }
        return latex;
      }

      if (op === '-') {
        const left = astToLatex(c[0], '-');
        const rightRaw = astToLatex(c[1], '-');
        const right = _needsParens(c[1], '-') ? `\\left(${rightRaw}\\right)` : rightRaw;
        const latex = `${left} - ${right}`;
        if (parentOp && PRECEDENCE['-'] < (PRECEDENCE[parentOp] ?? PRECEDENCE.atom)) {
          return `\\left(${latex}\\right)`;
        }
        return latex;
      }

      if (op === '*') {
        const leftRaw = astToLatex(c[0], '*');
        const rightRaw = astToLatex(c[1], '*');
        const left = _needsParens(c[0], '*') ? `\\left(${leftRaw}\\right)` : leftRaw;
        const right = _needsParens(c[1], '*') ? `\\left(${rightRaw}\\right)` : rightRaw;
        const latex = `${left} \\cdot ${right}`;
        if (parentOp && PRECEDENCE['*'] < (PRECEDENCE[parentOp] ?? PRECEDENCE.atom)) {
          return `\\left(${latex}\\right)`;
        }
        return latex;
      }

      if (op === '/') {
        const latex = `\\frac{${astToLatex(c[0], '/')}}{${astToLatex(c[1], '/')}}`;
        if (parentOp && PRECEDENCE['/'] < (PRECEDENCE[parentOp] ?? PRECEDENCE.atom)) {
          return `\\left(${latex}\\right)`;
        }
        return latex;
      }

      if (op === 'pow') {
        const base = c[0];
        const exp = astToLatex(c[1], 'pow');
        if (base && base.type === 'call' && ['sin', 'cos', 'tan', 'csc', 'sec', 'cot'].includes(base.op)) {
          return `\\${base.op}^{${exp}}\\left(${astToLatex(base.children[0], 'func')}\\right)`;
        }

        const baseRaw = astToLatex(base, 'pow');
        const baseLatex = _needsParens(base, 'pow') ? `\\left(${baseRaw}\\right)` : baseRaw;
        const latex = `{${baseLatex}}^{${exp}}`;
        if (parentOp && PRECEDENCE.pow < (PRECEDENCE[parentOp] ?? PRECEDENCE.atom)) {
          return `\\left(${latex}\\right)`;
        }
        return latex;
      }

      return `\\text{${op}}(${c.map(child => astToLatex(child)).join(', ')})`;
    }

    function sexprToLatex(sexpr) {
      if (!sexpr) return '';
      try {
        const tokens = tokenizeSexpr(sexpr);
        const [ast] = parseSexprAST(tokens, 0);
        return astToLatex(ast);
      } catch { return sexpr; }
    }

    function updatePreview(inputId, previewId) {
      const el = document.getElementById(previewId);
      const sexpr = getSexpr(inputId);
      if (!sexpr) {
        el.innerHTML = '';
        el.classList.add('empty');
        return;
      }
      el.classList.remove('empty');
      try {
        const latex = sexprToLatex(sexpr);
        katex.render(latex, el, { throwOnError: false, displayMode: false });
      } catch {
        el.textContent = sexpr;
      }
    }

    document.getElementById('input-lhs').addEventListener('input', () => updatePreview('input-lhs', 'preview-lhs'));
    document.getElementById('input-rhs').addEventListener('input', () => updatePreview('input-rhs', 'preview-rhs'));

    document.querySelectorAll('.mode-toggle button').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.mode-toggle button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        mode = btn.dataset.mode;
        updatePreview('input-lhs', 'preview-lhs');
        updatePreview('input-rhs', 'preview-rhs');
      });
    });

    const RULE_MAPPING = {
      'starting': 'Initial expression',
      'add-0': 'Simplify: a + 0 = a',
      'add-0-r': 'Simplify: 0 + a = a',
      'sub-0': 'Simplify: a - 0 = a',
      'sub-self': 'Simplify: a - a = 0',
      'mul-0': 'Simplify: a * 0 = 0',
      'mul-0-r': 'Simplify: 0 * a = 0',
      'mul-1': 'Simplify: a * 1 = a',
      'mul-1-r': 'Simplify: 1 * a = a',
      'div-1': 'Simplify: a / 1 = a',
      'div-self': 'Simplify: a / a = 1',
      'pow-0': 'Simplify: a^0 = 1',
      'pow-1': 'Simplify: a^1 = a',
      'one-pow': 'Simplify: 1^a = 1',
      'sub-to-neg': 'Rewrite: 0 - a = -a',
      'neg-neg': 'Simplify: -(-a) = a',
      'mul-neg-one': 'Rewrite: (-1)*a = -a',
      'div-neg-cancel': 'Simplify: (-a)/(-b) = a/b',
      'add-comm': 'Commutativity of addition',
      'add-assoc': 'Associativity of addition',
      'mul-comm': 'Commutativity of multiplication',
      'mul-assoc': 'Associativity of multiplication',
      'sub-to-add-neg': 'Rewrite subtraction as addition of a negative',
      'sub-sub': 'Rewrite: a - (b - c) = (a - b) + c',
      'neg-dist-add': 'Distribute a negative sign over addition',
      'pow-sq': 'Rewrite: a^2 = a*a',
      'pow-mul': 'Rewrite: (ab)^n = a^n b^n',
      'pow-div': 'Rewrite: (a/b)^n = a^n / b^n',
      'frac-mul': 'Multiply fractions',
      'frac-div': 'Divide fractions by multiplying by the reciprocal',
      'frac-nest-num': 'Simplify a nested fraction in the numerator',
      'frac-nest-den': 'Simplify a nested fraction in the denominator',
      'frac-cancel-1': 'Cancel a factor in a fraction product',
      'frac-cancel-2': 'Cancel a factor in a fraction product',
      'div-cancel-1': 'Cancel a common factor in a fraction',
      'div-cancel-2': 'Cancel a common factor in a fraction',
      'frac-reduce': 'Reduce a fraction by canceling a common factor',
      'add-frac-int': 'Add an integer and a fraction',
      'sub-frac-int': 'Subtract a fraction from an integer',
      'tan-def': 'Definition of tangent: tan(x) = sin(x)/cos(x)',
      'cot-def': 'Definition of cotangent: cot(x) = cos(x)/sin(x)',
      'sec-def': 'Definition of secant: sec(x) = 1/cos(x)',
      'csc-def': 'Definition of cosecant: csc(x) = 1/sin(x)',
      'pythag-1': 'Pythagorean identity: sin^2(x) + cos^2(x) = 1',
      'pythag-1-rev': 'Pythagorean identity: sin^2(x) + cos^2(x) = 1',
      'pythag-neg-csc': 'Identity: 1 - csc^2(x) = -cot^2(x)',
      'pythag-neg-sec': 'Identity: 1 - sec^2(x) = -tan^2(x)',
      'pythag-sin-sub': 'Identity: 1 - sin^2(x) = cos^2(x)',
      'pythag-cos-sub': 'Identity: 1 - cos^2(x) = sin^2(x)',
      'tan-sec': 'Identity: sec^2(x) = 1 + tan^2(x)',
      'sec2-sub-1': 'Identity: sec^2(x) - 1 = tan^2(x)',
      'cot-csc': 'Identity: csc^2(x) = 1 + cot^2(x)',
      'sin-cos-sq': 'Identity: sin^2(x) = 1 - cos^2(x)',
      'frac-add-cross': 'Add fractions by cross-multiplying',
      'frac-sub-cross': 'Subtract fractions by cross-multiplying',
      'frac-add-same-den': 'Add fractions with a common denominator',
      'frac-sub-same-den': 'Subtract fractions with a common denominator',
      'frac-div-same-den': 'Divide fractions with a common denominator',
      'diff-squares': 'Difference of squares',
      'sq-sub': 'Square of a difference',
      'sq-sum': 'Square of a sum',
      'sum-cubes': 'Sum of cubes factorization',
      'diff-cubes': 'Difference of cubes factorization',
      'pow-4': 'Rewrite a fourth power as a product of squares',
      'dist-left': 'Distribute multiplication over addition',
      'dist-right': 'Distribute multiplication over addition',
      'dist-sub-left': 'Distribute multiplication over subtraction',
      'dist-sub-right': 'Distribute multiplication over subtraction',
      'sec-tan-sq-sin': 'Rationalize (sec(x) - tan(x))^2',
      'tan-sec-sq-sin': 'Rationalize (tan(x) - sec(x))^2',
      'csc-frac-diff': 'Simplify a special cosecant fraction difference',
    };

    function getFancyRuleName(ruleId, rewriteDir) {
      if (!ruleId) return '';
      let reversed = false;

      let base = ruleId;
      if (base.endsWith('-rev')) {
        base = base.slice(0, -4);
        reversed = true;
      }

      if (rewriteDir === '<=') {
        reversed = !reversed;
      }

      const title = RULE_MAPPING[base] || base.replace(/-/g, ' ');
      return reversed ? `${title} (reverse direction)` : title;
    }

    function renderResult(data) {
      const container = document.getElementById('results');
      if (data.verified) {
        let stepsHtml = '';

        const filtered = [];
        let prevCanon = null;
        for (let i = 0; i < data.steps.length; i++) {
          const expr = data.steps[i];
          const canon = canonicalizeSexpr(expr);
          if (prevCanon !== null && canon === prevCanon) continue;
          filtered.push(expr);
          prevCanon = canon;
        }

        filtered.forEach((expr, i) => {
          const m = expr.match(/\(Rewrite([<=>]+)\s+([\w-]+)/);
          const rewriteDir = m ? m[1] : null;
          const ruleId = m ? m[2] : (i === 0 ? 'starting' : '');
          const ruleName = getFancyRuleName(ruleId, rewriteDir);
          const delay = (i + 1) * 60;
          const latex = sexprToLatex(expr);

          if (i > 0) stepsHtml += `<div class="proof-arrow" style="animation: fadeSlideUp 0.3s ease ${delay - 30}ms forwards; opacity: 0;">&darr;</div>`;
          stepsHtml += `<div class="proof-step" style="animation-delay: ${delay}ms; opacity: 0;"><div class="proof-header"><div class="proof-label">Step ${i + 1}</div><div class="proof-rule">${ruleName}</div></div><div class="proof-math" id="step-math-${i}"></div></div>`;
          setTimeout(() => {
            const el = document.getElementById(`step-math-${i}`);
            if (el) katex.render(latex, el, { throwOnError: false, displayMode: true });
          }, delay + 50);
        });
        container.innerHTML = `<div class="result"><div class="result-banner success"><span class="icon">&check;</span><div class="meta"><span>Identity Verified</span><small>${filtered.length} steps</small></div></div><div class="steps-title">Proof Derivation</div><div class="proof-container">${stepsHtml}</div></div>`;
      } else {
        const msg = (data.error || 'The identity could not be proven within search limits.').replace(/</g, '&lt;');
        container.innerHTML = `<div class="result"><div class="result-banner failure"><span class="icon">&times;</span><div class="meta"><span>Could Not Verify</span><small>${msg}</small></div></div></div>`;
      }
    }

    async function handleVerify() {
      const btn = document.getElementById('verify-btn');
      const lhs = getSexpr('input-lhs');
      const rhs = getSexpr('input-rhs');
      if (!lhs || !rhs) {
        renderResult({ verified: false, error: 'Please enter both sides of the identity.', steps: [] });
        return;
      }
      btn.classList.add('loading');
      btn.querySelector('.btn-text').textContent = 'Verifying...';
      try {
        const res = await fetch('/api/verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ lhs, rhs }),
        });
        const data = await res.json();
        renderResult(data);
      } catch (err) {
        renderResult({ verified: false, error: 'Failed to connect to the verification server.', steps: [] });
      } finally {
        btn.classList.remove('loading');
        btn.querySelector('.btn-text').textContent = 'Verify Identity';
      }
    }
  </script>
</body>

</html>
""".encode('utf-8')
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Expires', '0')
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
        if self.path == '/api/verify':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                payload = json.loads(body) if body else {}
            except json.JSONDecodeError:
                payload = {}

            lhs = (payload.get('lhs') or '').strip()
            rhs = (payload.get('rhs') or '').strip()

            if not lhs or not rhs:
                response = {"verified": False, "steps": [], "error": "Missing lhs or rhs."}
            else:
                run = _run_verifier(lhs, rhs)
                response = {"verified": run["verified"], "steps": run["steps"], "error": run["error"]}

            res = json.dumps(response).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(res)))
            self.end_headers()
            self.wfile.write(res)
            self.wfile.flush()
            return

        if self.path == '/verify':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length).decode('utf-8')
            params = urllib.parse.parse_qs(post_data)
            
            expr1 = params.get('expr1',[''])[0]
            expr2 = params.get('expr2', [''])[0]

            run = _run_verifier(expr1, expr2)
            output = run["raw"]

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
    print(f"Web server successfully running on: http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        server.server_close()