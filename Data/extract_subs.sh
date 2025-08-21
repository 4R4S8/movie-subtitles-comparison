#!/bin/bash

# Find all zip files and process them
find . -type f -name "*.zip" | while read -r zipfile; do
    # Get the parent directory of the zip file
    parent_dir=$(dirname "$zipfile")
    
    # Create the english directory if it doesn't exist
    english_dir="${parent_dir}/english"
    mkdir -p "$english_dir"
    
    # Extract the zip file into the english directory
    unzip -q -o "$zipfile" -d "$english_dir"
    
    echo "Extracted $zipfile to $english_dir"
done
