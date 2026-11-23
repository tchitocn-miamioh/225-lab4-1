
FROM python:3.9-slim

# Install required system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nfs-common && \
    rm -rf /var/lib/apt/lists/*

# Set application working directory
WORKDIR /app

# Create mount point for persistent storage
RUN mkdir -p /nfs

# Copy Python dependencies
COPY requirements.txt .

# Install Flask and Gunicorn
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Configure application environment
ENV PORT=5000
ENV DATABASE_PATH=/nfs/demo.db
ENV PYTHONUNBUFFERED=1

# Expose application port
EXPOSE 5000

# Initialize SQLite database and start Gunicorn
CMD ["sh", "-c", "python -c 'from main import init_db; init_db()' && exec gunicorn --bind 0.0.0.0:5000 --workers 1 main:app"]
