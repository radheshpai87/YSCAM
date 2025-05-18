#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test script to verify the model loading and inference pipeline.
This is useful for debugging model deployment issues.
"""

import os
import sys
import pickle
import numpy as np
from data_preparation import DataPreparation
from logistic_model import LogisticModel

def test_model_loading():
    """Test loading the model from the models directory"""
    model_path = "models/logistic_regression_model.pkl"
    
    if not os.path.exists(model_path):
        print(f"ERROR: Model file does not exist: {model_path}")
        print(f"Working directory: {os.getcwd()}")
        if os.path.exists("models"):
            print(f"Files in models directory: {os.listdir('models')}")
        else:
            print("Models directory does not exist")
        return False
    
    print(f"Model file found: {model_path} (size: {os.path.getsize(model_path)} bytes)")
    
    try:
        # Load model from file
        with open(model_path, 'rb') as f:
            model_dict = pickle.load(f)
            
        model = model_dict.get('model')
        vectorizer = model_dict.get('vectorizer')
        
        if model is None:
            print("ERROR: Model not found in the pickle file")
            return False
            
        if vectorizer is None:
            print("ERROR: Vectorizer not found in the pickle file")
            return False
            
        print(f"Model loaded successfully: {type(model).__name__}")
        print(f"Vectorizer loaded successfully: {type(vectorizer).__name__}")
        
        # Test prediction
        test_messages = [
            "Capgemini is hiring for customer support. Apply via official career page.",
            "Urgent hiring for marketing intern at TCS. instant approval. Apply now via unauthorized portal.",
            "Urgent hiring for marketing intern at HCL. pay registration fee. Apply now via WhatsApp link."
        ]
        
        # Preprocess test messages
        data_prep = DataPreparation()
        processed_messages = [data_prep.preprocess_text(msg) for msg in test_messages]
        
        # Transform messages using vectorizer
        test_features = vectorizer.transform(processed_messages)
        
        # Make predictions
        predictions = model.predict(test_features)
        probabilities = model.predict_proba(test_features)
        
        # Show results
        print("\nTest Message Classifications:")
        for i, message in enumerate(test_messages):
            prediction = "FAKE" if predictions[i] == 1 else "REAL"
            confidence = np.max(probabilities[i])
            print(f"{i+1}. \"{message[:40]}...\" -> {prediction} (confidence: {confidence:.2f})")
        
        print("\nModel verification completed successfully")
        return True
        
    except Exception as e:
        print(f"ERROR during model testing: {e}")
        import traceback
        traceback.print_exc()
        return False
        

if __name__ == "__main__":
    success = test_model_loading()
    if not success:
        print("Model verification FAILED")
        sys.exit(1)
    else:
        print("Model verification PASSED")
        sys.exit(0)
