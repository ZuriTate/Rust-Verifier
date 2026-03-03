#!/bin/bash
set -euo pipefail

# Use writable directories (Render's /usr/local/cargo can be read-only)
export CARGO_HOME="/tmp/cargo"
export RUSTUP_HOME="/tmp/rustup"
export CARGO_NET_GIT_FETCH_WITH_CLI="true"
export CARGO_REGISTRIES_CRATES_IO_PROTOCOL="sparse"
export PATH="${CARGO_HOME}/bin:${PATH}"

# Extra safety: ensure cargo registry/git caches also go to /tmp
mkdir -p "${CARGO_HOME}" "${RUSTUP_HOME}" /tmp/cargo-home
export CARGO_TARGET_DIR="/tmp/target"

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

# Copy the built binary back into the repo workspace so the web app can run it
if [ -f "/tmp/target/release/trig_verifier" ]; then
  cp "/tmp/target/release/trig_verifier" "./trig_verifier"
  chmod +x "./trig_verifier" || true
fi
