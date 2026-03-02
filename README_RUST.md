# Rust Binary Integration

## Current Status
The app now has full Rust integration! Here's how it works:

1. **Primary**: Uses the actual Rust binary if available
2. **Fallback**: Shows mock results if binary is missing

## Binary Locations Checked
- `./target/release/trig_verifier` (local build)
- `./trig_verifier` (copied to root)
- `/app/trig_verifier` (Docker path)

## To Add Real Rust Binary

### Option 1: Compile for Linux (Recommended)
```bash
# Install Linux target
rustup target add x86_64-unknown-linux-gnu

# Compile for Linux
cargo build --release --target x86_64-unknown-linux-gnu

# Copy to repo root
cp target/x86_64-unknown-linux-gnu/release/trig_verifier ./trig_verifier

# Make executable
chmod +x trig_verifier

# Commit
git add trig_verifier
git commit -m "Add Linux Rust binary"
git push origin main
```

### Option 2: Use Docker
```bash
# Build using Docker
docker run --rm -v "$(pwd)":/app rust:1.75 cargo build --release

# Copy binary
cp target/release/trig_verifier ./trig_verifier
chmod +x trig_verifier
```

## Features
- ✅ Full UI with KaTeX rendering
- ✅ Step filtering (removes +0, redundant steps)
- ✅ Mathematician-readable rule names
- ✅ Rust backend integration
- ✅ Graceful fallback to mock data

## Test Identities
- `sec^4(x) - sec^2(x)` = `tan^2(x) + tan^4(x)`
- `sin^2(x) + cos^2(x)` = `1`
- `sec(x) + csc(x) - cos(x) - sin(x)` = `tan(x) + cot(x)`
