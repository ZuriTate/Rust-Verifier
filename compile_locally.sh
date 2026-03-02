#!/bin/bash
# Compile Rust binary locally for deployment
echo "Compiling Rust binary for Linux deployment..."
cargo build --release --target x86_64-unknown-linux-gnu
echo "Binary compiled: target/x86_64-unknown-linux-gnu/release/trig_verifier"
echo "Copy this to your repo root as 'trig_verifier'"
