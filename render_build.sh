#!/bin/bash
# Render build script to ensure Docker is properly used

echo "===== RENDER BUILD SCRIPT STARTED ====="
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

# Check if running in Render
if [ -n "$RENDER" ]; then
  echo "Running on Render platform"
  
  # Check if Docker is available
  if command -v docker &> /dev/null; then
    echo "Docker is available on this system"
    docker --version
    
    # Try to build Docker image directly
    echo "Attempting to build Docker image..."
    docker build -t scam-detection-api .
    
    if [ $? -eq 0 ]; then
      echo "Docker image built successfully"
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
