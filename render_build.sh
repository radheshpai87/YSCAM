#!/bin/bash
# Render build script to ensure Docker is properly used

echo "===== RENDER BUILD SCRIPT STARTED ====="
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# Create diagnostic information for debugging
echo "===== ENVIRONMENT DIAGNOSTICS ====="
echo "Operating system: $(uname -a)"
echo "User: $(whoami)"
echo "PATH: $PATH"
echo "RENDER: $RENDER"
echo "OCR_ENABLED: $OCR_ENABLED"
echo "DOCKER_DEPLOYMENT: $DOCKER_DEPLOYMENT"

# Create a .env file for lightweight OCR configuration
echo "Creating .env file for environment configuration"
echo "OCR_ENABLED=True" > .env
echo "OCR_API_KEY=${OCR_API_KEY:-K87589515488957}" >> .env
echo "DOCKER_DEPLOYMENT=True" >> .env
echo ".env file created with contents:"
cat .env

# Check for Tesseract in the environment (might not be available during build)
echo "===== CHECKING FOR TESSERACT ====="
if command -v tesseract &> /dev/null; then
    echo "Tesseract is available in PATH"
    tesseract --version
    tesseract --list-langs
else
    echo "Tesseract NOT found in PATH during build"
    # Check common locations
    for path in /usr/bin/tesseract /usr/local/bin/tesseract /app/usr/bin/tesseract; do
        if [ -f "$path" ] && [ -x "$path" ]; then
            echo "Found Tesseract at: $path"
            $path --version
        fi
    done
fi

# Check if running in Render
if [ -n "$RENDER" ]; then
  echo "Running on Render platform"
  
  # Verify render.yaml file
  if [ -f "render.yaml" ]; then
      echo "render.yaml file exists:"
      cat render.yaml
  else
      echo "WARNING: render.yaml file not found!"
  fi
  
  # Verify Dockerfile
  if [ -f "Dockerfile" ]; then
      echo "Dockerfile exists and contains:"
      cat Dockerfile
  else
      echo "WARNING: Dockerfile not found!"
  fi
  
  # Check if Docker is available
  if command -v docker &> /dev/null; then
    echo "Docker is available on this system"
    docker --version
    
    # Try to build Docker image directly
    echo "Attempting to build Docker image..."
    docker build -t scam-detection-api .
    
    if [ $? -eq 0 ]; then
      echo "Docker image built successfully"
      docker images
      
      # Try running a test container to verify Tesseract is installed
      echo "Running test container to verify Tesseract..."
      docker run --rm scam-detection-api tesseract --version
    else
      echo "Docker build failed, will rely on Render's Docker handling"
    fi
  else
    echo "Docker is not available in this environment"
    echo "Render should handle Docker build automatically based on render.yaml"
  fi
else
  echo "Not running on Render platform"
fi

echo "===== RENDER BUILD SCRIPT COMPLETED ====="

# Exit successfully to allow render.yaml to continue with deployment
exit 0
