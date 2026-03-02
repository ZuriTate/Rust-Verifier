#!/bin/bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source $HOME/.cargo/env

# Clear cache and build
export CARGO_HOME=/tmp/cargo
export RUSTUP_HOME=/tmp/rustup
cargo cache --clear
cargo build --release
