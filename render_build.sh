#!/bin/bash
set -euo pipefail

# Use writable directories (Render's /usr/local/cargo can be read-only)
export CARGO_HOME="${CARGO_HOME:-/tmp/cargo}"
export RUSTUP_HOME="${RUSTUP_HOME:-/tmp/rustup}"
export PATH="${CARGO_HOME}/bin:${PATH}"

# Ensure a C compiler exists (needed by some Rust crates)
if ! command -v cc >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update
    apt-get install -y build-essential
  fi
fi

# Install Rust (into CARGO_HOME/RUSTUP_HOME)
if ! command -v cargo >/dev/null 2>&1; then
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path
fi

# Make sure rustup/cargo are on PATH for this shell
if [ -f "${CARGO_HOME}/env" ]; then
  # shellcheck disable=SC1090
  source "${CARGO_HOME}/env"
fi

rustc --version
cargo --version

# Build the verifier
cargo build --release
chmod +x target/release/trig_verifier || true
