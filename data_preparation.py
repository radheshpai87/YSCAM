#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import re
import emoji
import nltk
import os
import sys
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.model_selection import train_test_split

# Custom tokenizer function as a fallback
def safe_tokenize(text):
    """
    A safe tokenization function that works without requiring NLTK resources.
    Falls back to simple splitting if NLTK word_tokenize fails.
    """
    try:
        return word_tokenize(text)
    except LookupError:
        # Simple but effective tokenization
        # First, ensure spaces around punctuation so they get split properly
        text = re.sub(r'([.,!?;:])', r' \1 ', text)
        # Then split by whitespace and filter out empty strings
        return [token for token in text.split() if token.strip()]

# Ensure NLTK resources are downloaded
def ensure_nltk_resources():
    """Download required NLTK resources with better error handling"""
    # Dictionary mapping resource names to their actual paths in NLTK
    resource_paths = {
        'punkt': 'tokenizers/punkt',
        'stopwords': 'corpora/stopwords',
        'wordnet': 'corpora/wordnet',
        'omw-1.4': 'corpora/omw-1.4'
    }
    
    resources = ['punkt', 'stopwords', 'wordnet', 'omw-1.4']
    for resource in resources:
        path = resource_paths.get(resource, f'tokenizers/{resource}')
        try:
            print(f"Checking NLTK resource: {resource}")
            nltk.data.find(path)
            print(f"Resource {resource} already downloaded")
        except LookupError:
            print(f"Downloading NLTK resource: {resource}")
            try:
                nltk.download(resource, quiet=False)
                print(f"Successfully downloaded {resource}")
            except Exception as e:
                print(f"Error downloading {resource}: {e}")
                print("You may need to manually download NLTK resources.")
                print("Try running: python install_nltk_resources.py")
                # Continue without exiting - we'll use fallbacks

# Download required NLTK resources
ensure_nltk_resources()

class DataPreparation:
    def __init__(self, random_state=42):
        self.random_state = random_state
        
        # Set up stopwords with error handling
        try:
            self.stop_words = set(stopwords.words('english'))
        except Exception as e:
            print(f"Warning: Could not load NLTK stopwords: {e}")
            # Fallback to minimal stopword set
            self.stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 
                             'to', 'of', 'for', 'in', 'on', 'at', 'by', 'with', 
                             'about', 'as', 'is', 'am', 'are', 'was', 'were', 'be', 
                             'been', 'being', 'have', 'has', 'had', 'do', 'does', 
                             'did', 'will', 'would', 'shall', 'should', 'can', 'could', 
                             'may', 'might', 'must', 'this', 'that', 'these', 'those'}
        
        # Set up lemmatizer with error handling
        try:
            self.lemmatizer = WordNetLemmatizer()
        except Exception as e:
            print(f"Warning: Could not initialize WordNetLemmatizer: {e}")
            # We'll handle this in the preprocess_text method
    
    def load_data(self, file_path):
        """Load data from CSV file"""
        try:
            # Check if the file has labels
            df = pd.read_csv(file_path)
            
            # For the new dataset, map 'predicted_label' to 'label'
            if 'predicted_label' in df.columns and 'label' not in df.columns:
                print(f"Found 'predicted_label' column, using as 'label' column")
                df['label'] = df['predicted_label'] 
            # If there's no 'label' column, we assume it's unlabeled data
            elif 'label' not in df.columns:
                print(f"Warning: No 'label' column found in {file_path}")
                
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
    
    def preprocess_text(self, text, remove_stopwords=True, lemmatize=True):
        """
        Preprocess text by:
        1. Converting to lowercase
        2. Removing URLs
        3. Removing email addresses
        4. Removing phone numbers
        5. Expanding contractions (like you're → you are)
        6. Removing special characters and punctuation
        7. Removing emojis
        8. Removing stopwords (optional)
        9. Lemmatizing (optional)
        """
        if not isinstance(text, str):
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove phone numbers
        text = re.sub(r'\b(?:\+\d{1,3}[- ]?)?\d{10}\b|\b\d{3}[-.\s]??\d{3}[-.\s]??\d{4}\b', '', text)
        
        # Expand common contractions - add this step before removing punctuation
        contraction_patterns = {
            r"won\'t": "will not",
            r"can\'t": "cannot",
            r"n\'t": " not",
            r"\'re": " are",
            r"\'s": " is",
            r"\'d": " would",
            r"\'ll": " will",
            r"\'t": " not",
            r"\'ve": " have",
            r"\'m": " am"
        }
        
        for pattern, repl in contraction_patterns.items():
            text = re.sub(pattern, repl, text)
        
        # Remove currency symbols and numbers with currency symbols
        text = re.sub(r'[$₹€£¥](\d+([,.]\d+)?)|(\d+([,.]\d+)?)[$₹€£¥]', '', text)
        
        # Remove special characters and punctuation
        text = re.sub(r'[^\w\s]', '', text)
        
        # Remove emojis
        text = emoji.replace_emoji(text, replace='')
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Tokenization using safe_tokenize
        tokens = safe_tokenize(text)
        
        # Remove stopwords
        if remove_stopwords:
            try:
                tokens = [word for word in tokens if word not in self.stop_words]
            except Exception as e:
                # If stopwords aren't available, create a minimal stopwords set
                print(f"Warning: NLTK stopwords not available ({e}). Using minimal stopword set.")
                minimal_stopwords = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 
                                    'to', 'of', 'for', 'in', 'on', 'at', 'by', 'with', 
                                    'about', 'as', 'is', 'am', 'are', 'was', 'were', 'be', 
                                    'been', 'being', 'have', 'has', 'had', 'do', 'does', 
                                    'did', 'will', 'would', 'shall', 'should', 'can', 'could', 
                                    'may', 'might', 'must', 'this', 'that', 'these', 'those'}
                tokens = [word for word in tokens if word not in minimal_stopwords]
        
        # Lemmatize
        if lemmatize:
            try:
                tokens = [self.lemmatizer.lemmatize(word) for word in tokens]
            except Exception as e:
                # If lemmatizer isn't available, use a minimal rule-based approach
                print(f"Warning: NLTK lemmatization not available ({e}). Using simple suffix removal.")
                # Simple rule-based lemmatization (very basic)
                simple_lemmatizer = lambda w: w[:-1] if w.endswith('s') else w
                tokens = [simple_lemmatizer(word) for word in tokens]
        
        # Join tokens back into a string
        text = ' '.join(tokens)
        
        return text
    
    def prepare_data(self, df, text_column='message', label_column='label', test_size=0.2, val_size=0.25):
        """
        Prepare data for model training:
        1. Preprocess text
        2. Split into train, validation, and test sets
        """
        # Preprocess text
        df['processed_text'] = df[text_column].apply(self.preprocess_text)
        
        # If label column exists, convert to binary
        if label_column in df.columns:
            # Check which label format is being used
            if df[label_column].iloc[0].lower() in ['real', 'scam']:
                # Original label format: 'real' or 'scam'
                df['binary_label'] = df[label_column].map({'real': 0, 'scam': 1})
            elif df[label_column].iloc[0].lower() in ['likely genuine', 'requires caution']:
                # New label format: 'likely genuine' or 'requires caution'
                df['binary_label'] = df[label_column].map({'likely genuine': 0, 'requires caution': 1})
                # Also create a compatible 'label' column for compatibility with existing code
                df['label'] = df[label_column].map({'likely genuine': 'real', 'requires caution': 'scam'})
            else:
                print(f"WARNING: Unrecognized label format: {df[label_column].iloc[0]}")
                print("Assuming binary classification with 0 and 1")
                # Try to convert to numeric if possible, otherwise use string mapping
                try:
                    df['binary_label'] = pd.to_numeric(df[label_column])
                except:
                    unique_labels = df[label_column].unique()
                    if len(unique_labels) == 2:
                        label_map = {unique_labels[0]: 0, unique_labels[1]: 1}
                        df['binary_label'] = df[label_column].map(label_map)
                        print(f"Created mapping: {label_map}")
                    else:
                        raise ValueError(f"Cannot automatically map {len(unique_labels)} unique labels to binary values")
            
            # Split data
            # First split into train+val and test
            train_val, test = train_test_split(
                df, test_size=test_size, random_state=self.random_state, stratify=df['binary_label']
            )
            
            # Then split train+val into train and val
            train, val = train_test_split(
                train_val, 
                test_size=val_size,  # This is relative to train_val
                random_state=self.random_state,
                stratify=train_val['binary_label']
            )
            
            return train, val, test
        else:
            # For unlabeled data, just return the processed dataframe
            print("No label column found. Returning processed dataframe without splitting.")
            return df, None, None
    
    def standardize_labels(self, df, label_column='label'):
        """
        Standardize labels from various formats to the expected 'real'/'scam' format.
        This handles both the original format and the new dataset format.
        """
        if label_column not in df.columns:
            print(f"Warning: No '{label_column}' column found in dataframe")
            return df

        # Sample the first few values to determine the format
        sample_labels = df[label_column].dropna().head(5).tolist()
        
        if len(sample_labels) == 0:
            print("Warning: No labels available in the dataset")
            return df
            
        # Check if we need to standardize
        if all(label.lower() in ['real', 'scam'] for label in sample_labels if isinstance(label, str)):
            print("Labels are already in standard format ('real'/'scam')")
            return df
        
        # Check if we have the new format
        if any(label.lower() in ['likely genuine', 'requires caution'] for label in sample_labels if isinstance(label, str)):
            print("Converting 'likely genuine'/'requires caution' labels to 'real'/'scam'")
            label_map = {'likely genuine': 'real', 'requires caution': 'scam'}
            df['label'] = df[label_column].map(label_map)
            print(f"Created label column with mapping: {label_map}")
        else:
            print(f"Unknown label format: {sample_labels}")
            print("Please specify a mapping for these labels.")
            
        return df
        
    def create_synthetic_labels(self, df, text_column='message', keywords=None):
        """
        Create synthetic labels for unlabeled data based on keywords.
        This is a simple rule-based approach for demonstration purposes.
        In a real scenario, you would want to manually label data.
        """
        if keywords is None:
            # Default keywords that might indicate scams
            keywords = {
                'scam': ['pay', 'confirm', 'money', 'urgent', 'free', 'offer', 'limited', 
                         'won', 'winning', 'prize', 'claim', 'cash', 'fee', 'fees', 'payment',
                         'verify', 'verification', 'deposit', 'guarantee', 'risk-free',
                         'easy money', 'make money', 'earn from home', 'work from home',
                         'no interview', 'without interview', 'today', 'immediate',
                         'send', 'transfer', 'lottery', 'award', 'selected', 'exclusive']
            }
        
        def label_message(message):
            message_lower = message.lower()
            for word in keywords['scam']:
                if word.lower() in message_lower:
                    return 'scam'
            return 'real'
        
        df['label'] = df[text_column].apply(label_message)
        
        # Print distribution of synthetic labels
        print(f"Created synthetic labels: {df['label'].value_counts().to_dict()}")
        
        return df


if __name__ == "__main__":
    # Example usage
    data_prep = DataPreparation()
    
    # Load data
    file_path = "scam_detection_unlabeled_extended.csv"
    df = data_prep.load_data(file_path)
    
    if df is not None:
        # Create synthetic labels for demonstration
        df = data_prep.create_synthetic_labels(df)
        
        # Prepare data
        train_df, val_df, test_df = data_prep.prepare_data(df)
        
        # Save processed datasets
        train_df.to_csv("train_data.csv", index=False)
        val_df.to_csv("val_data.csv", index=False)
        test_df.to_csv("test_data.csv", index=False)
        
        print(f"Train set size: {len(train_df)}")
        print(f"Validation set size: {len(val_df)}")
        print(f"Test set size: {len(test_df)}")
