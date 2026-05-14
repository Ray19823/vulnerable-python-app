FROM python:3.8-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY test_app.py .

# Create a non-root user (we'll improve this in remediation)
RUN useradd -m appuser

# Expose port
EXPOSE 5000

# Run the application (running as root for now - vulnerability!)
CMD ["python", "app.py"]
