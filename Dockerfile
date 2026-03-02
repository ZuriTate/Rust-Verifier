# Use Python base with Rust installed
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and Rust
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Copy source code
COPY Cargo.toml Cargo.lock ./
COPY src ./src
COPY server.py ./

# Build Rust binary
RUN export CARGO_HOME=/tmp/cargo && \
    export RUSTUP_HOME=/tmp/rustup && \
    cargo cache --clear && \
    cargo build --release

# Make binary executable
RUN chmod +x target/release/trig_verifier

# Start the server
CMD ["python", "server.py"]
