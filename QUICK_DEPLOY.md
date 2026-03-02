# 🚀 Quick Deploy to Free Hosting

## Option 1: Render.com (Easiest - 5 minutes)

1. **Go to https://render.com/**
2. **Sign up** (free with GitHub)
3. **Click "New +" → "Web Service"**
4. **Connect GitHub** → Select "Rust-Verifier" repo
5. **Configure:**
   - Name: `trig-verifier`
   - Environment: `Docker`
   - Branch: `master`
   - Root Directory: `.` (leave blank)
6. **Click "Deploy"**

That's it! Render will:
- Build your Rust binary automatically
- Deploy the Python server
- Give you a URL like: `https://trig-verifier.onrender.com`

## Option 2: Railway (Also Free)

1. **Go to https://railway.app/**
2. **Sign up** with GitHub
3. **Click "Deploy from GitHub repo"**
4. **Select "Rust-Verifier"**
5. **Add environment variable:** `PORT=8080`
6. **Click "Deploy"**

## Option 3: Replit (Testing Only)

1. **Go to https://replit.com/github/ZuriTate/Rust-Verifier**
2. **Fork the repo**
3. **Run:** `python server.py`

## What I've Set Up For You

✅ **Dockerfile** - Builds Rust + runs Python server  
✅ **Cross-platform paths** - Works on Linux/Mac/Windows  
✅ **Environment variables** - Uses PORT from hosting service  
✅ **All files pushed** to your GitHub repo  

## Test These Identities

After deployment, try:
- `sec^4(x) - sec^2(x)` = `tan^2(x) + tan^4(x)`
- `sin^2(x) + cos^2(x)` = `1`
- `sec(x) + csc(x) - cos(x) - sin(x)` = `tan(x) + cot(x)`

## Free Tier Limits

- **Render:** 750 hours/month (enough for 24/7)
- **Railway:** $5 credit/month (plenty for this app)
- **Replit:** Limited but great for testing

## Troubleshooting

If deployment fails:
1. Check the build logs
2. Make sure `Cargo.toml` is in the repo
3. Verify the Docker can find `trig_verifier` binary

The app should be live in 3-5 minutes! 🎉
