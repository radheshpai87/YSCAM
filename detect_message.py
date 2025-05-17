#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import pickle
import numpy as np
import re
from data_preparation import DataPreparation

def load_model(model_path):
    """Load a trained model from file"""
    try:
        with open(model_path, 'rb') as f:
            model_dict = pickle.load(f)
        return model_dict.get('model'), model_dict.get('vectorizer')
    except Exception as e:
        print(f"Error loading model: {e}")
        return None, None

def has_high_risk_signals(text):
    """Check for high-risk signals in the text that are strong indicators of scams"""
    text_lower = text.lower()
    
    # Check for legitimate context words that would make registration normal
    legitimate_context = any(word in text_lower for word in ["university portal", "official portal", "careers portal", "college", "university"])
    
    # Don't apply high-risk patterns if legitimate context is found
    if legitimate_context:
        return []
    
    # List of high-risk patterns common in job/loan scams
    high_risk_patterns = [
        # Payment requests combined with jobs
        (r'(job|work|hiring|position|opening).{0,30}(pay|fee|rs|₹|payment).{0,30}([0-9]{3,})', 
         "Job offers requiring payment for registration, assessment, or application are almost always scams"),
        
        # Work from home with high earnings
        (r'(work from home|earn from home).{0,30}(₹|rs).?\d{3,}', 
         "Promises of high earnings from work-at-home jobs without specific skills are typical scam tactics"),
        
        # No interview job offers
        (r'(job|work|position).{0,30}(no interview|without interview)', 
         "Legitimate companies don't offer jobs without some form of assessment"),
        
        # Requesting sensitive documents via message
        (r'(send|share|submit).{0,30}(aadhar|pan|account|bank details|password|otp)',
         "Legitimate organizations don't request sensitive personal documents or financial details via messages"),
         
        # Money for registration
        (r'(registration fee|apply fee|pay.{0,5}(for|to).{0,10}(register|registration))',
         "Requiring payment for registration is a common scam tactic"),
         
        # Requesting payment with specific amounts (with exclusions for false positives)
        (r'pay.{0,5}(₹|rs).{0,5}[0-9]{3,}',
         "Requesting specific payment amounts in job or loan messages is a red flag")
    ]
    
    # Check for high-risk patterns
    risk_signals = []
    for pattern, explanation in high_risk_patterns:
        if re.search(pattern, text_lower):
            risk_signals.append(explanation)
    
    return risk_signals

def get_prediction(model, text, vectorizer, word_embeddings=None):
    """Get prediction for a text message"""
    # For English text, use standard preprocessing
    data_prep = DataPreparation()
    processed_text = data_prep.preprocess_text(text)
    
    # Generate features using TF-IDF vectorizer
    features = vectorizer.transform([processed_text])
    
    # Get prediction and confidence
    prediction = model.predict(features)
    
    # Get confidence score (probability)
    confidence = model.predict_proba(features)
    confidence_score = max(confidence[0])
    
    # Map prediction to label
    label = "scam" if prediction[0] == 1 else "real"
    
    # Get important features for explanation
    feature_importance = {}
    
    # Extract word importance based on model
    coefficients = model.coef_[0]
    feature_names = vectorizer.get_feature_names_out()
    
    # Get non-zero features in the input
    input_vector = features.toarray()[0]
    non_zero_idx = np.where(input_vector > 0)[0]
    
    # Extract words and their coefficients
    for idx in non_zero_idx:
        if idx < len(feature_names):
            word = feature_names[idx]
            importance = coefficients[idx] * input_vector[idx]
            feature_importance[word] = importance
    
    # Sort by absolute importance
    sorted_features = sorted(
        feature_importance.items(), 
        key=lambda x: abs(x[1]), 
        reverse=True
    )[:5]  # Get top 5 features
    
    return label, confidence_score, sorted_features

def main():
    parser = argparse.ArgumentParser(description='Scam Detection for User Input')
    parser.add_argument('--message', type=str, help='Message to classify (enclose in quotes)')
    parser.add_argument('--model', type=str, default='logistic_regression', 
                        help='Model to use for classification')
    parser.add_argument('--debug', action='store_true', help='Show additional debug information')
    
    args = parser.parse_args()
    
    if args.message:
        # One-time classification mode
        model_path = f"models/logistic_regression_model.pkl"
        model, vectorizer = load_model(model_path)
        
        if model is None:
            print(f"Error: Could not load model from {model_path}")
            return
        
        # Check for high-risk signals before model prediction
        risk_signals = has_high_risk_signals(args.message)
        
        # Get model prediction
        label, confidence, important_features = get_prediction(model, args.message, vectorizer)
        
        # If high-risk signals are found, override with high confidence scam classification
        if risk_signals and label == "real" and confidence < 0.75:
            label = "scam"
            confidence = max(confidence, 0.85)  # Set minimum confidence to 85%
        
        # Display result
        print(f"\nMessage: {args.message}")
        print(f"Classification: {label.upper()}")
        
        # Create visual confidence meter
        confidence_pct = int(confidence * 100)
        bars = int(confidence_pct / 10)
        confidence_bar = "▓" * bars + "░" * (10 - bars)
        print(f"Confidence: {confidence:.2%} [{confidence_bar}]")
        
        # Display high-risk signals if found
        if risk_signals:
            print("\n🚨 HIGH-RISK SIGNALS DETECTED:")
            for signal in risk_signals:
                print(f"  • {signal}")
        
        # Display key indicators that influenced the decision
        if important_features:
            print("\nKey indicators:")
            for word, importance in important_features:
                indicator_type = "Scam indicator" if importance > 0 else "Legitimate indicator"
                print(f"  • '{word}': {indicator_type} (weight: {abs(importance):.4f})")
    else:
        # Interactive mode
        print("\n=========================================")
        print("  SCAM DETECTION TERMINAL")
        print("=========================================")
        print("Enter messages to check if they're scams.")
        print("Commands:")
        print("  • 'quit' or 'exit': Exit the program")
        print("  • Type any message to analyze it")
        print("This system uses logistic regression to identify potential scams.")
        
        # Load the Logistic Regression model
        model_path = "models/logistic_regression_model.pkl"
        model, vectorizer = load_model(model_path)
        
        if model is None:
            print(f"Error: Could not load model from {model_path}")
            return
        
        # Interactive loop
        try:
            while True:
                user_input = input("\nEnter message (or 'exit' to quit): ")
                if user_input.lower() in ['quit', 'exit', '']:
                    print("\nExiting scam detection. Goodbye!")
                    break
                    
                message = user_input
                    
                # Get prediction
                try:
                    # Check for high-risk signals before model prediction
                    risk_signals = has_high_risk_signals(message)
                    
                    # Get model prediction
                    label, confidence, important_features = get_prediction(model, message, vectorizer)
                    
                    # If high-risk signals are found, override with high confidence scam classification
                    if risk_signals and label == "real" and confidence < 0.75:
                        label = "scam"
                        confidence = max(confidence, 0.85)  # Set minimum confidence to 85%
                    
                    # Display results with colored output and visual confidence indicator
                    result_symbol = "❌" if label == "scam" else "✅"
                    result_border = "!" if label == "scam" else "="
                    print(f"\n{result_border * 50}")
                    print(f"RESULT: {result_symbol} This message is classified as: {label.upper()}")
                    print(f"{result_border * 50}")
                    
                    # Create visual confidence meter
                    confidence_pct = int(confidence * 100)
                    bars = int(confidence_pct / 10)
                    confidence_bar = "▓" * bars + "░" * (10 - bars)
                    print(f"Confidence: {confidence:.2%} [{confidence_bar}]")
                    
                    # Display high-risk signals if found
                    if risk_signals:
                        print("\n🚨 HIGH-RISK SIGNALS DETECTED:")
                        for signal in risk_signals:
                            print(f"  • {signal}")
                    
                    # Display key indicators that influenced the decision
                    if important_features:
                        print("\nKey indicators:")
                        for word, importance in important_features:
                            indicator_type = "Scam indicator" if importance > 0 else "Legitimate indicator"
                            # Use a visual indicator for scam/legitimate features
                            icon = "⚠️" if importance > 0 else "✓"
                            print(f"  • {icon} '{word}': {indicator_type} (weight: {abs(importance):.4f})")
                        
                except Exception as e:
                    print(f"Error processing message: {e}")
                    
        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Exiting scam detection.")
        except EOFError:
            print("\n\nEnd of input. Exiting scam detection.")

if __name__ == "__main__":
    main()
