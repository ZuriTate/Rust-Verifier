# Build stage for Rust binary
FROM rust:1.75 as builder

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src

# Clear cache and build
RUN cargo cache --clear && cargo build --release

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
RUN pip install --no-cache-dir subprocess

# Copy the compiled Rust binary from builder stage
COPY --from=builder /app/target/release/trig_verifier /app/trig_verifier

# Copy Python server
COPY server.py ./

# Make the binary executable
RUN chmod +x trig_verifier

# Expose port
EXPOSE 8080

# Run the Python server
CMD ["python", "server.py"]
