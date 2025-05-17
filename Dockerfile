FROM python:3.11

# Install Tesseract OCR
RUN apt-get update && \
    apt-get install -y tesseract-ocr tesseract-ocr-eng && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Download NLTK resources
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4');"

# Copy the rest of the code
COPY . .

# Create temp directory
RUN mkdir -p ./tmp

# Expose port
ENV PORT=10000
EXPOSE $PORT

# Run the application with Gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT wsgi:app
