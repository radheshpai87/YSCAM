FROM python:3.11-slim

# Install Tesseract OCR and other dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify Tesseract installation
RUN tesseract --version

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

# Make sure build scripts are executable
RUN chmod +x build.sh
RUN chmod +x verify_tesseract.sh

# Verify Tesseract installation is working properly
RUN ./verify_tesseract.sh > tesseract_verification.log

# Set PYTHONPATH to include the app directory
ENV PYTHONPATH=/app
ENV PORT=10000
ENV TESSERACT_AVAILABLE=True
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE $PORT

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:$PORT/ || exit 1

# Run the application with Gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT wsgi:app --log-level=info --log-file=-
