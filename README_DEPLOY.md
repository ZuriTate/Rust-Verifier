# Deploy Trig Verifier to Free Hosting

## Option 1: Render.com (Recommended - Free Rust Support)

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Add deployment files"
git push origin main
```

### Step 2: Deploy to Render
1. Go to https://render.com/
2. Sign up for free account
3. Click "New +" → "Web Service"
4. Connect your GitHub repo: https://github.com/ZuriTate/Rust-Verifier
5. Select "Docker" environment
6. Use the `Dockerfile` I created
7. Deploy!

Render will:
- Build the Rust binary automatically
- Run the Python server
- Give you a public URL like `https://trig-verifier.onrender.com`

## Option 2: Railway (Also Free)

### Step 1: Install Railway CLI
```bash
npm install -g @railway/cli
```

### Step 2: Deploy
```bash
railway login
railway init
railway up
```

## Option 3: Replit (Easiest but Limited)

1. Go to https://replit.com/
2. Create new Repl from your GitHub repo
3. Add these files to the Repl
4. Run `python server.py`

## What I Added

- `Dockerfile`: Builds Rust binary + runs Python server
- `render.yaml`: Render.com deployment config
- Modified `server.py` to work with Linux paths

## Testing

After deployment, test with:
- `sec^4(x) - sec^2(x)` = `tan^2(x) + tan^4(x)`
- `sin^2(x) + cos^2(x)` = `1`

The free tiers have limits but should work fine for this app!
