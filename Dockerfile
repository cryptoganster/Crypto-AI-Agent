# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python packages to user directory
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini .

# ============================================
# Stage 2: Development
# ============================================
FROM python:3.11-slim AS development

WORKDIR /app

# Install system dependencies for development
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install ALL dependencies (including dev dependencies)
RUN pip install --no-cache-dir -r requirements.txt

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest>=7.4.3 \
    pytest-asyncio>=0.21.1 \
    pytest-cov>=4.1.0 \
    pytest-mock>=3.12.0 \
    hypothesis>=6.92.0 \
    black>=23.11.0 \
    isort>=5.12.0 \
    flake8>=6.1.0 \
    mypy>=1.7.1 \
    watchfiles

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# ⚠️ NO copiar src/ - se monta como volumen en docker-compose
# Esto permite hot-reload cuando cambias archivos

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 0

# Development with hot-reload
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================
# Stage 3: Production
# ============================================
FROM python:3.11-slim AS production

# Build arguments para metadata
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION=dev

# Labels de metadata (OCI Image Spec)
LABEL org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.authors="TradingApp Team" \
      org.opencontainers.image.url="https://github.com/tradingapp/tradingapp" \
      org.opencontainers.image.documentation="https://github.com/tradingapp/tradingapp/blob/main/README.md" \
      org.opencontainers.image.source="https://github.com/tradingapp/tradingapp" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.vendor="TradingApp" \
      org.opencontainers.image.title="Scraping Service" \
      org.opencontainers.image.description="Servicio de scraping y análisis de contenido web con Playwright" \
      com.tradingapp.service.name="scraping-service" \
      com.tradingapp.service.type="microservice" \
      com.tradingapp.service.ports.http="8000" \
      com.tradingapp.service.language="python"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# Install Playwright browsers
RUN /root/.local/bin/playwright install chromium
RUN /root/.local/bin/playwright install-deps chromium

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Add local bin to PATH
ENV PATH=/root/.local/bin:$PATH

# Set production environment
ENV ENVIRONMENT=production

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
