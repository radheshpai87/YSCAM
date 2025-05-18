# Machine Learning-Based Scam Detection System

This project implements a machine learning-based text classification system that can detect whether a job or loan offer message is real or a scam. The system uses logistic regression with TF-IDF features for efficient and explainable classification.

## Overview

The system leverages logistic regression with TF-IDF vectorization to classify text messages as either "real" or "scam". It provides a complete pipeline from data preparation to model evaluation and explainability.

## Key Features

- **Text Classification**: Analyzes the content of messages to detect scam patterns
- **Risk Pattern Detection**: Uses rule-based patterns to identify high-risk signals
- **Document Processing**: Extracts text from various document formats (PDF, DOCX, images)
- **Lightweight OCR**: Uses cloud-based OCR service for efficient text extraction from images
- **REST API**: Provides an API for easy integration with other systems
- **Detailed Explanations**: Provides human-readable explanations of classifications

## Lightweight OCR Implementation

This system uses a cloud-based OCR solution via the OCRSpace API instead of local Tesseract for several advantages:

- **Performance**: Significantly faster processing time compared to local Tesseract OCR
- **Reliability**: No more "Tesseract process timeout" errors on resource-constrained environments
- **Compatibility**: Works well with Render's free tier without memory/CPU limitations
- **Maintenance**: No need to install or maintain complex OCR binaries

The OCR system includes:

- Intelligent caching to reduce API calls
- Automatic image optimization for better OCR results
- Fallback mechanisms when OCR is unavailable
- Support for JPEG, PNG, and BMP image formats

For more details, see [Lightweight OCR Documentation](LIGHTWEIGHT_OCR_README.md).

## API Access

The system includes a RESTful API that allows you to use the scam detection capabilities via HTTP requests:

```bash
# Install dependencies
pip install -r requirements.txt

# Start the API in development mode
python run_api.py

# Or in production mode with multiple workers
python run_api.py --production --workers 4
```

### API Documentation

#### Endpoints

1. **Health Check**

   - **URL**: `/health`
   - **Method**: `GET`
   - **Description**: Check if the API is operating correctly
   - **Response Example**:
     ```json
     {
       "status": "ok",
       "timestamp": 1747459689.133,
       "model": "logistic_regression"
     }
     ```

2. **Text Classification**

   - **URL**: `/detect`
   - **Method**: `POST`
   - **Content Type**: `application/json`
   - **Request Body**:
     ```json
     {
       "message": "Your message text here"
     }
     ```
   - **Response Example**:
     ```json
     {
       "message": "Your message text here",
       "classification": "real",
       "confidence": 0.92,
       "confidence_percentage": "92.00%",
       "important_features": [
         {
           "term": "word1",
           "indicator_type": "Legitimate indicator",
           "weight": 0.35
         }
       ],
       "explanations": ["This message was classified as legitimate because..."]
     }
     ```
   - **Response Fields**:
     - `classification`: Either "scam" or "real"
     - `confidence`: Probability score between 0 and 1
     - `confidence_percentage`: Human-readable confidence percentage
     - `important_features`: Words that influenced the classification
     - `explanations`: Human-readable explanations for the classification
     - `high_risk_signals`: (Only for scams) Additional risk signals detected

3. **Document Upload Classification**
   - **URL**: `/upload`
   - **Method**: `POST`
   - **Content Type**: `multipart/form-data`
   - **Form Data**:
     - `file`: PDF, DOCX, or image file containing text to analyze
   - **Supported File Types**: PDF, DOCX, DOC, JPG, JPEG, PNG, BMP, TIFF
   - **Response**: Same as text classification, with an additional `filename` field

### Usage Examples

**Classify a Text Message:**

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"message": "JOB OPPORTUNITY: Work from home and earn Rs.25000 weekly. Registration fee Rs.500 only."}' \
  http://localhost:5000/detect
```

**Upload a Document for Classification:**

```bash
curl -X POST \
  -F "file=@/path/to/document.pdf" \
  http://localhost:5000/upload
```

## Command Line Usage

You can also use the system directly from the command line:

```bash
# Check a specific message
python detect_message.py --message "Your message text here"

# Enter interactive mode
python detect_message.py
```

## Technical Details

- **Algorithm**: Logistic Regression
- **Feature Extraction**: TF-IDF Vectorization
- **Text Preprocessing**: Lowercasing, tokenization, stop word removal
- **Document Processing**: PDF, DOCX, and image text extraction

## Dependencies

This project requires the following main dependencies:

- NumPy, pandas
- scikit-learn
- Flask & Flask-CORS
- PyMuPDF, python-docx, Pillow, requests (for document processing and OCR)
- NLTK

See `requirements.txt` for a complete list.

## Setup

1. Clone the repository
2. Install the dependencies: `pip install -r requirements.txt`
3. Ensure you have trained models in the `models` directory
4. Run the API: `python run_api.py`

## Deployment on Render

This application can be easily deployed on Render's cloud platform:

### Prerequisites

1. Create a free Render account at https://render.com
2. Connect your GitHub/GitLab repository containing this project

### Deployment Steps - Method 1: Using Web Service

1. In your Render dashboard, click on "New" and select "Web Service"
2. Connect to your repository and select the branch you want to deploy
3. Configure the following settings:

   - **Name**: scam-detection-api (or your preferred name)
   - **Environment**: Python
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT wsgi:app`
   - **Plan**: Free (or select a paid plan for better performance)
   - **Python Version**: 3.11

4. Click "Create Web Service"

### Deployment Steps - Method 2: Using Docker (Recommended)

1. In your Render dashboard, click on "New" and select "Web Service"
2. Connect to your repository and select the branch you want to deploy
3. Configure the following settings:

   - **Name**: scam-detection-api (or your preferred name)
   - **Environment**: Docker
   - **Plan**: Free (or select a paid plan for better performance)

4. Click "Create Web Service"

This Docker-based approach ensures that Tesseract OCR is properly installed and available for image processing.

Render will automatically:

- Install system dependencies like Tesseract OCR
- Install Python dependencies from requirements.txt
- Start the application with Gunicorn

### Environment Variables

The following environment variables can be configured:

- `PORT`: The port on which the application runs (default: 10000)

### Scaling Considerations

- The free plan has limited resources and goes to sleep after inactivity
- For production use, consider upgrading to a paid plan
- Large model files may exceed free plan storage limits

### Known Limitations

- **OCR Functionality**: The system now uses a lightweight API-based OCR solution instead of Tesseract.

  - OCR functionality is provided via OCRSpace API with free tier key (K87589515488957)
  - The free tier allows up to 500 API calls per day
  - For higher volume usage, update the OCR API key as described in OCR_API_KEY_SETUP.md
  - If the API is unreachable, the system will gracefully degrade to use image metadata

- **Sleep Mode**: On the free tier, the service goes to sleep after inactivity, causing a delay on first request
  - The first request after inactivity may take up to 30 seconds to respond
  - Subsequent requests will be much faster

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Future Plans for Improvements

- Implementing a more robust and scalable architecture for handling large volumes of images
- Enhancing the model's accuracy through fine-tuning and incorporating additional features

## API Key Security

The OCR functionality uses OCRSpace API, which requires an API key. For security:

- The API key is set as an environment variable and not stored in the codebase
- In development, use the .env file (not committed to Git) to store your API key
- In production, set the OCR_API_KEY environment variable on your server
- For Render deployment, the API key is set in the environment variables section

Never commit your API keys to version control.
