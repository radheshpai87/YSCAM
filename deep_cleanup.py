#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Deep cleanup of the SCAM detection system to focus only on essential files
for the logistic regression model implementation.
"""

import os
import shutil
import sys

# Define the essential files needed for the system to work
ESSENTIAL_FILES = [
    # Core functionality
    'logistic_model.py',
    'detect_message.py',
    'api.py',
    'file_api.py',
    'run_api.py',
    'document_processor.py',
    'data_preparation.py',
    
    # Configuration and requirements
    'requirements.txt',
    'runtime.txt',
    
    # Documentation
    'README.md',
    'API_DOCUMENTATION.md',
    
    # Model files
    'models/logistic_regression_model.pkl',
    
    # Initial setup
    'install_nltk_resources.py',
    
    # This cleanup script
    'deep_cleanup.py'
]

# Define directories to keep
ESSENTIAL_DIRS = [
    'models',
    '__pycache__'
]

def backup_file(filepath):
    """Create a backup of a file with .bak extension if it doesn't already exist"""
    backup_path = f"{filepath}.bak"
    if not os.path.exists(backup_path):
        try:
            shutil.copy2(filepath, backup_path)
            print(f"Created backup: {backup_path}")
        except Exception as e:
            print(f"Error backing up {filepath}: {str(e)}")

def remove_file(filepath, dry_run=False):
    """Remove a file with backup"""
    if os.path.exists(filepath):
        if filepath.endswith('.bak'):
            # Don't make backups of backups
            if not dry_run:
                os.remove(filepath)
                print(f"Removed backup: {filepath}")
            else:
                print(f"[DRY RUN] Would remove backup: {filepath}")
        else:
            # Backup and remove regular files
            if not dry_run:
                backup_file(filepath)
                os.remove(filepath)
                print(f"Removed: {filepath}")
            else:
                print(f"[DRY RUN] Would remove: {filepath}")
    else:
        print(f"File does not exist: {filepath}")

def is_essential(filepath):
    """Check if a file is in the essential files list"""
    filepath = filepath.replace('\\', '/')  # Normalize path separators
    
    # Check if it's an essential file directly
    if filepath in ESSENTIAL_FILES:
        return True
    
    # Check if it's in an essential directory
    for dir_path in ESSENTIAL_DIRS:
        if filepath.startswith(f"{dir_path}/"):
            return True
    
    return False

def cleanup_directory(directory, dry_run=False):
    """Clean up a directory by removing non-essential files"""
    print(f"\nCleaning up directory: {directory}")
    
    # Convert to absolute paths for consistency
    abs_directory = os.path.abspath(directory)
    abs_essential_files = [os.path.join(abs_directory, f) for f in ESSENTIAL_FILES]
    
    # Collect all files
    all_files = []
    for root, dirs, files in os.walk(abs_directory):
        for file in files:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, abs_directory)
            all_files.append((file_path, rel_path))
    
    # Remove non-essential files
    removed_count = 0
    for abs_path, rel_path in all_files:
        if not is_essential(rel_path) and not any(rel_path.startswith(d) for d in ESSENTIAL_DIRS):
            remove_file(abs_path, dry_run)
            removed_count += 1
    
    return removed_count

def main():
    """Main function to perform the cleanup"""
    # Parse arguments
    dry_run = '--dry-run' in sys.argv
    
    # Print mode
    if dry_run:
        print("\n=== DRY RUN MODE - No files will actually be removed ===\n")
    else:
        print("\n=== LIVE MODE - Files will be removed ===\n")
    
    # Get base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    
    print(f"Working in directory: {base_dir}")
    
    # Step 1: Perform the cleanup
    removed_count = cleanup_directory(base_dir, dry_run)
    
    # Step 2: Summary
    print("\n=== Cleanup Summary ===")
    print(f"Total files removed: {removed_count}")
    print("\nRemaining essential files:")
    for file in ESSENTIAL_FILES:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ✗ {file} (missing)")
    
    print("\nCleanup completed successfully!")
    print("The system has been simplified to include only essential files.")
    print("Backups of all removed files were created with .bak extension.")
    print("\nTo complete the cleanup and remove backups, run:")
    print("find . -name '*.bak' -delete")

if __name__ == "__main__":
    main()
