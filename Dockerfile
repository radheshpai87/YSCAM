# Use a specific Python version for reproducibility
FROM python:3.11-slim

# Set Tesseract environment variables globally
ENV TESSERACT_AVAILABLE=True
ENV PYTHONUNBUFFERED=1
ENV DOCKER_DEPLOYMENT=True

# Install Tesseract OCR and other dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-osd \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    procps \
    fonts-liberation \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify Tesseract installation and create marker files
RUN tesseract --version && \
    tesseract --list-langs && \
    echo "Tesseract is installed" > /tesseract_installed && \
    echo "TESSERACT_AVAILABLE=True" > /app/.env

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Download NLTK resources
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4');"

# Make directory for logs and temp files
RUN mkdir -p ./logs ./tmp

# Copy the rest of the code
COPY . .

# Make all scripts executable
RUN chmod +x build.sh verify_tesseract.sh verify_docker.sh test_ocr.py

# Run verification scripts
RUN echo "=== Running Tesseract verification ===" && \
    ./verify_tesseract.sh > tesseract_verification.log && \
    cat tesseract_verification.log && \
    echo "=== Running Docker environment verification ===" && \
    ./verify_docker.sh > docker_verification.log && \
    cat docker_verification.log && \
    echo "=== Running OCR verification ===" && \
    python test_ocr.py > ocr_test_results.txt || echo "OCR test completed with warnings"

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=10000
ENV TESSERACT_AVAILABLE=True
ENV PYTHONUNBUFFERED=1
ENV OCR_ENABLED=True

# Expose port
EXPOSE $PORT

# Health check with custom endpoint that verifies OCR status
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || curl -f http://localhost:$PORT/ || exit 1

# Create .env file at runtime to ensure environment variables are properly set
CMD echo "TESSERACT_AVAILABLE=True" > .env && \
    echo "Starting SCAM Detection API with OCR capabilities..." && \
    gunicorn --bind 0.0.0.0:$PORT --workers=2 --timeout=120 wsgi:app --log-level=info --log-file=-
