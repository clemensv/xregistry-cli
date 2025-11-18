# Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . .

# Build the package
RUN pip install --no-cache-dir build wheel && \
    python -m build --sdist --wheel --outdir dist

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy built wheels from builder
COPY --from=builder /build/dist /tmp/dist

# Install xregistry package
RUN pip install --no-cache-dir /tmp/dist/*.whl && \
    rm -rf /tmp/dist

# Create a non-root user for security
RUN useradd -m -u 1001 xregistry && \
    chown -R xregistry:xregistry /app

USER xregistry

# Set the entrypoint
ENTRYPOINT ["xregistry"]
CMD ["--help"]

# Labels for container metadata
LABEL org.opencontainers.image.title="xRegistry CLI" \
      org.opencontainers.image.description="A command-line tool for xRegistry with code generation for messaging and eventing applications" \
      org.opencontainers.image.vendor="CNCF" \
      org.opencontainers.image.source="https://github.com/clemensv/xregistry-cli"
