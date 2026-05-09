# Use official Python 3.12 slim image for a lightweight, secure foundation
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py

# Set work directory
WORKDIR /app

# Install dependencies
# We copy just the requirements.txt first to leverage Docker cache
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Expose the port Gunicorn will listen on
EXPOSE 5000

# Run gunicorn (4 workers is usually good for a simple proxy)
# Binding to 0.0.0.0 is necessary for Docker
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
