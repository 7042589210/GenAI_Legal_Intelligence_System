# Use lightweight Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install OS-level dependencies required for OCR and other operations
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt and install Python dependencies
# Assuming requirements.txt is at the root of the context
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend source code
COPY backend /app/backend

# Set environment variables for production
ENV PYTHONPATH=/app
ENV TESSERACT_CMD=/usr/bin/tesseract

# Expose port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
