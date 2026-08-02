# Small, current Python base image
FROM python:3.12-slim

# PYTHONUNBUFFERED: logs appear immediately (not buffered) - important for
#   container log streaming.
# PYTHONDONTWRITEBYTECODE: skip writing .pyc files in the container.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Copy and install dependencies FIRST, on their own layer. Docker caches this
# layer and only rebuilds it when requirements.txt changes - faster rebuilds.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application code.
COPY producer.py .

# Run as a non-root user (security best practice - containers shouldn't run
# as root unless they must).
RUN useradd --create-home appuser
USER appuser

# The command that runs when the container starts.
CMD ["python", "producer.py"]
