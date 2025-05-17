#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NLTK Resource Downloader

This script downloads all the necessary NLTK data resources required for the
scam detection project.
"""

import nltk
import os
import sys

def download_nltk_resources():
    """Download all required NLTK resources"""
    required_resources = [
        'punkt',
        'stopwords', 
        'wordnet',
        'omw-1.4',  # Open Multilingual WordNet
        'averaged_perceptron_tagger',  # For POS tagging
        'maxent_ne_chunker',  # Named entity recognition
        'words'  # Words corpus
    ]
    
    print("Starting download of NLTK resources...")
    
    for resource in required_resources:
        print(f"Downloading {resource}...")
        try:
            nltk.download(resource)
            print(f"Successfully downloaded {resource}")
        except Exception as e:
            print(f"Error downloading {resource}: {e}")
    
    # Verify resources were installed
    print("\nVerifying installed resources:")
    resource_paths = {
        'punkt': 'tokenizers/punkt',
        'stopwords': 'corpora/stopwords',
        'wordnet': 'corpora/wordnet',
        'omw-1.4': 'corpora/omw-1.4'
    }
    
    for resource in required_resources:
        try:
            nltk.data.find(resource_paths.get(resource, resource))
            print(f"✓ {resource} is installed")
        except LookupError:
            print(f"✗ {resource} was not properly installed")
    
    print("\nNLTK resources download complete.")
    print("If there were any errors, you may need to manually download the resources:")
    print("import nltk; nltk.download()")

if __name__ == "__main__":
    download_nltk_resources()
