FROM python:3.11-slim

# Metadata
LABEL maintainer="HealthOpsEnv"
LABEL description="OpenEnv-compatible healthcare operations simulation environment"

# Set working directory
WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (7860 = HuggingFace Spaces standard)
EXPOSE 7860

# Environment variables with defaults
ENV PORT=7860
ENV HOST=0.0.0.0
ENV LOG_LEVEL=info

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:7860/health').raise_for_status()"

# Start server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860", "--log-level", "info"]
