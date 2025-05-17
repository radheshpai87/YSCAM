#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import pickle
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

class LogisticModel:
    def __init__(self, random_state=42):
        self.random_state = random_state
        self.model = None
        self.vectorizer = None
        self.performance = {}
    
    def train_logistic_regression(self, X_train, y_train):
        """Train Logistic Regression with TF-IDF"""
        start_time = time.time()
        
        # Create TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(max_features=10000)
        
        # Fit the vectorizer
        X_train_tfidf = self.vectorizer.fit_transform(X_train)
        
        # Create and fit the logistic regression model
        self.model = LogisticRegression(random_state=self.random_state, max_iter=1000, C=1.0)
        self.model.fit(X_train_tfidf, y_train)
        
        training_time = time.time() - start_time
        self.performance['training_time'] = training_time
        
        return self.model, self.vectorizer
    
    def evaluate_model(self, X, y_true):
        """Evaluate the model and return predictions and metrics"""
        if self.model is None or self.vectorizer is None:
            raise ValueError("Model or vectorizer not initialized. Train or load a model first.")
        
        start_time = time.time()
        
        # Transform input with TF-IDF
        X_features = self.vectorizer.transform(X)
        
        # Get predictions
        y_pred = self.model.predict(X_features)
        
        # Get prediction probabilities (confidence scores)
        y_proba = self.model.predict_proba(X_features)
        confidence_scores = np.max(y_proba, axis=1)
        
        # Calculate metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred)
        recall = recall_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred)
        conf_matrix = confusion_matrix(y_true, y_pred)
        
        inference_time = time.time() - start_time
        
        # Store metrics
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': conf_matrix,
            'inference_time': inference_time
        }
        self.performance.update(metrics)
        
        return y_pred, confidence_scores, metrics
    
    def save_model(self, file_path):
        """Save the trained model and vectorizer to a file"""
        if self.model is None or self.vectorizer is None:
            raise ValueError("No model or vectorizer to save")
        
        # Create a dictionary with model and vectorizer
        save_dict = {
            'model': self.model,
            'vectorizer': self.vectorizer
        }
        
        # Save to file
        with open(file_path, 'wb') as f:
            pickle.dump(save_dict, f)
        
        print(f"Model saved to {file_path}")
    
    def load_model(self, file_path):
        """Load a trained model and its vectorizer from a file"""
        try:
            with open(file_path, 'rb') as f:
                load_dict = pickle.load(f)
            
            self.model = load_dict.get('model')
            self.vectorizer = load_dict.get('vectorizer')
            
            if self.model is None:
                raise ValueError("No model found in the file")
            if self.vectorizer is None:
                raise ValueError("No vectorizer found in the file")
            
            print(f"Model loaded from {file_path}")
            return self.model, self.vectorizer
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return None, None


if __name__ == "__main__":
    # Example usage
    train_df = pd.read_csv("train_data.csv")
    val_df = pd.read_csv("val_data.csv")
    
    # Initialize model
    log_model = LogisticModel()
    
    # Train model
    log_model.train_logistic_regression(train_df['processed_text'], train_df['binary_label'])
    
    # Evaluate model
    _, _, metrics = log_model.evaluate_model(val_df['processed_text'], val_df['binary_label'])
    print("\nLOGISTIC REGRESSION METRICS:")
    for metric, value in metrics.items():
        if metric != 'confusion_matrix':
            print(f"{metric}: {value}")
        else:
            print(f"{metric}:\n{value}")
    
    # Save model
    log_model.save_model('logistic_regression_model.pkl')
