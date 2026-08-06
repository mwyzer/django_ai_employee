# Dockerfile — production-ready multi-stage build
# Stage 1: Build
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim-bookworm

WORKDIR /app

# Install runtime system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r coolbreeze && useradd -r -g coolbreeze coolbreeze

# Copy only what's needed from builder
COPY --from=builder /root/.local /home/coolbreeze/.local
COPY . .

# Ensure scripts in .local are usable
ENV PATH=/home/coolbreeze/.local/bin:$PATH

# Collect static files
RUN DJANGO_SECRET_KEY=build-key-not-used DJANGO_DEBUG=0 ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput

# Switch to non-root user
USER coolbreeze

# Run with Uvicorn ASGI
CMD ["uvicorn", "dj_ai_employee_main.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
