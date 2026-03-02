#!/bin/bash
# Install Rust if not already installed
if ! command -v cargo &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
fi

# Build the Rust binary
export CARGO_HOME=/tmp/cargo
export RUSTUP_HOME=/tmp/rustup
cargo build --release

# Start the Python server
python server.py
