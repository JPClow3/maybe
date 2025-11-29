# syntax = docker/dockerfile:1

# Use Python 3.11 slim image
ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim AS base

# Django app lives here
WORKDIR /app

# Install base packages
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    curl \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set production environment
ARG BUILD_COMMIT_SHA
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=maybe_django.settings \
    BUILD_COMMIT_SHA=${BUILD_COMMIT_SHA}

# Throw-away build stage to reduce size of final image
FROM base AS build

# Install packages needed to build Python packages
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY maybe_django/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Copy application code
COPY maybe_django/ /app/

# Final stage for app image
FROM base

# Re-declare ARG for this stage
ARG PYTHON_VERSION=3.11

# Copy built artifacts: Python packages, application
# Copy to temp location first, then use RUN to move with variable expansion
# (COPY doesn't expand variables, but RUN does)
COPY --from=build /usr/local/lib /tmp/lib
COPY --from=build /usr/local/bin /tmp/bin
COPY --from=build /app /tmp/app

# Move to final location with variable expansion
RUN mkdir -p /usr/local/lib/python${PYTHON_VERSION}/site-packages && \
    cp -r /tmp/lib/python${PYTHON_VERSION}/site-packages/* /usr/local/lib/python${PYTHON_VERSION}/site-packages/ && \
    cp -r /tmp/bin/* /usr/local/bin/ && \
    cp -r /tmp/app/* /app/ && \
    rm -rf /tmp/lib /tmp/bin /tmp/app

# Run and own only the runtime files as a non-root user for security
RUN groupadd --system --gid 1000 django && \
    useradd django --uid 1000 --gid 1000 --create-home --shell /bin/bash && \
    chmod +x /app/bin/docker-entrypoint && \
    chown -R django:django /app
USER 1000:1000

# Entrypoint prepares the database
ENTRYPOINT ["/app/bin/docker-entrypoint"]

# Start the server by default, this can be overwritten at runtime
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
