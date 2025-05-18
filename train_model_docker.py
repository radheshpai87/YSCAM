#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to train the logistic regression model during Docker build process.
This ensures the model is already trained when deployed on Render.
"""

import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from logistic_model import LogisticModel
from data_preparation import DataPreparation

def train_model():
    print("=== Starting model training during Docker build ===")
    
    # Check if the dataset file exists
    dataset_file = "yscam_massive_dataset.csv"
    if not os.path.exists(dataset_file):
        print(f"Error: Dataset file '{dataset_file}' not found.")
        return False
    
    try:
        # Load and preprocess data
        print(f"Loading dataset from {dataset_file}...")
        df = pd.read_csv(dataset_file)
        print(f"Dataset loaded successfully with {len(df)} records.")
        
        # Data preprocessing
        print("Preprocessing text data...")
        data_prep = DataPreparation()
        df['processed_text'] = df['message'].apply(lambda x: data_prep.preprocess_text(x))
        
        # Convert categorical labels to binary
        print("Converting labels to binary...")
        df['binary_label'] = df['label'].apply(lambda x: 1 if x.lower() == 'fake' else 0)
        
        # Split data
        print("Splitting dataset into training and validation sets...")
        train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['binary_label'])
        
        print(f"Training set size: {len(train_df)}")
        print(f"Validation set size: {len(val_df)}")
        
        # Initialize and train the model
        print("Initializing Logistic Regression model...")
        log_model = LogisticModel()
        
        print("Training model...")
        log_model.train_logistic_regression(train_df['processed_text'], train_df['binary_label'])
        
        # Evaluate the model
        print("Evaluating model on validation set...")
        _, _, metrics = log_model.evaluate_model(val_df['processed_text'], val_df['binary_label'])
        
        print("\nLOGISTIC REGRESSION METRICS:")
        for metric, value in metrics.items():
            if metric != 'confusion_matrix':
                print(f"{metric}: {value}")
            else:
                print(f"{metric}:\n{value}")
        
        # Create models directory if it doesn't exist
        os.makedirs('models', exist_ok=True)
        
        # Save the model
        model_path = 'models/logistic_regression_model.pkl'
        print(f"Saving model to {model_path}...")
        log_model.save_model(model_path)
        
        print("=== Model training completed successfully ===")
        return True
        
    except Exception as e:
        print(f"Error during model training: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = train_model()
    if not success:
        print("Model training failed.")
        sys.exit(1)
    else:
        print("Model training succeeded.")
        sys.exit(0)
