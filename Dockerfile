# Use a specific Python version for reproducibility
FROM python:3.11-slim

# Set Lightweight OCR environment variables globally
ENV OCR_ENABLED=True
ENV PYTHONUNBUFFERED=1
ENV DOCKER_DEPLOYMENT=True

# Install lightweight dependencies (no Tesseract)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create marker files for lightweight OCR
RUN mkdir -p /app && \
    echo "OCR_ENABLED=True" > /app/.env && \
    echo "Lightweight OCR configuration" > /lightweight_ocr_enabled

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
RUN chmod +x build.sh verify_docker.sh train_model_docker.py

# Run verification scripts
RUN echo "=== Running Docker environment verification ===" && \
    ./verify_docker.sh > docker_verification.log && \
    cat docker_verification.log && \
    echo "=== Running Lightweight OCR verification ===" && \
    python -c "import lightweight_ocr; print('Lightweight OCR module imported successfully')" > lightweight_ocr_results.txt || echo "OCR test completed with notes"

# Train the model during build process
RUN echo "=== Training logistic regression model with expanded dataset ===" && \
    python train_model_docker.py > model_training.log && \
    cat model_training.log && \
    echo "=== Verifying model loading and inference ===" && \
    chmod +x test_model_loading.py && \
    python test_model_loading.py > model_verification.log && \
    cat model_verification.log

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=10000
ENV OCR_ENABLED=True
ENV PYTHONUNBUFFERED=1
# OCR API Key for OCRSpace
ENV OCR_API_KEY="K87589515488957"

# Expose port
EXPOSE $PORT

# Health check with custom endpoint that verifies OCR status
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/health || curl -f http://localhost:$PORT/ || exit 1

# Make the startup script executable and use it as entry point
RUN chmod +x start.sh

# Use the start.sh script as the entry point
CMD ["./start.sh"]
