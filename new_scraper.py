#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile
import shutil
import re
from pathlib import Path
import mimetypes
import datetime

def is_binary_file(file_path):
    """Check if a file is binary based on its extension and content."""
    # Check by extension first
    excluded_extensions = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp',  # Images
        '.dll', '.exe', '.bin', '.so', '.dylib',  # Executables and binaries
        '.onnx', '.tensorrt', '.pt', '.pth', '.h5', '.pb',  # ML models
        '.zip', '.tar', '.gz', '.xz', '.7z', '.rar',  # Archives
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',  # Documents
        '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',  # Media
        '.db', '.sqlite', '.dat'  # Data files
    }
    
    if any(file_path.lower().endswith(ext) for ext in excluded_extensions):
        return True
    
    # Check by mime type
    mime, _ = mimetypes.guess_type(file_path)
    if mime is None:
        # If mimetype can't be determined, read a small chunk and check for null bytes
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except:
            return True  # If we can't read the file, consider it binary
    
    # Consider text-based mime types
    text_mimes = ['text/', 'application/json', 'application/xml', 'application/javascript', 
                 'application/x-python', 'application/x-ruby', 'application/x-php']
    
    return not any(text_type in mime for text_type in text_mimes)

def get_file_info(file_path):
    """Get additional file information."""
    stat = os.stat(file_path)
    size = stat.st_size
    modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    
    # Count lines safely
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = sum(1 for _ in f)
    except:
        lines = "N/A"  # Unable to count lines
    
    return {
        'size': size,
        'modified': modified,
        'lines': lines
    }

def main():
    # Check if the correct number of arguments is provided
    if len(sys.argv) != 2:
        print("Usage: github_scraper.py [https://github.com/username/repository.git]")
        sys.exit(1)
    
    # Get the GitHub repository URL
    repo_url = sys.argv[1]
    
    # Convert github.com URLs to git format if needed
    if 'github.com' in repo_url and not repo_url.endswith('.git'):
        repo_url = repo_url + '.git'
    
    # Validate GitHub URL
    if not re.match(r'https?://github\.com/[^/]+/[^/]+/?.*', repo_url):
        print("Error: Invalid GitHub repository URL")
        sys.exit(1)
    
    # Extract repository name from URL for output file naming
    repo_name = repo_url.split('/')[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    
    # Create a temporary directory to clone the repository
    temp_dir = tempfile.mkdtemp()
    print(f"Using temporary directory: {temp_dir}")
    
    try:
        # Clone the repository
        print(f"Cloning repository {repo_url}...")
        try:
            result = subprocess.run(['git', 'clone', repo_url, temp_dir], 
                                   stderr=subprocess.PIPE, stdout=subprocess.PIPE, 
                                   universal_newlines=True)
            if result.returncode != 0:
                print(f"Error cloning repository: {result.stderr}")
                sys.exit(1)
        except Exception as e:
            print(f"Failed to execute git clone: {str(e)}")
            sys.exit(1)
        
        # Output file path
        output_file_path = f"{repo_name}_content.txt"
        
        # Set maximum file size to process (10 MB)
        MAX_FILE_SIZE = 10 * 1024 * 1024
        
        # Collect files
        print("Collecting files...")
        file_info = []
        for root, dirs, files in os.walk(temp_dir):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, temp_dir)
                
                # Check if file is binary
                if is_binary_file(file_path):
                    print(f"Skipping binary file: {rel_path}")
                    continue
                
                # Get file size
                try:
                    size = os.path.getsize(file_path)
                    if size > MAX_FILE_SIZE:
                        print(f"Skipping large file: {rel_path} ({size / 1024 / 1024:.2f} MB)")
                        continue
                    
                    file_info.append({
                        'path': rel_path,
                        'size': size
                    })
                except Exception as e:
                    print(f"Error accessing file {rel_path}: {str(e)}")
        
        # Sort file information by path
        file_info.sort(key=lambda x: x['path'])
        
        # Process the repository and write to the output file
        print(f"Writing content to {output_file_path}...")
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            # Write header
            output_file.write(f"# Repository: {repo_url}\n")
            output_file.write(f"# Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Write table of contents
            output_file.write("## Table of Contents\n\n")
            for i, info in enumerate(file_info, 1):
                path = info['path']
                size_kb = info['size'] / 1024
                output_file.write(f"{i}. {path} ({size_kb:.2f} KB)\n")
            
            # Process each file
            for info in file_info:
                rel_path = info['path']
                file_path = os.path.join(temp_dir, rel_path)
                
                try:
                    # Get additional file info
                    additional_info = get_file_info(file_path)
                    
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Write file information and content to output file
                    output_file.write(f"\n\n{'='*80}\n")
                    output_file.write(f"File: {rel_path}\n")
                    output_file.write(f"Size: {additional_info['size'] / 1024:.2f} KB | ")
                    output_file.write(f"Lines: {additional_info['lines']} | ")
                    output_file.write(f"Last Modified: {additional_info['modified']}\n")
                    output_file.write(f"{'='*80}\n\n")
                    output_file.write(content)
                except UnicodeDecodeError:
                    output_file.write(f"\n\n{'='*80}\n")
                    output_file.write(f"File: {rel_path}\n")
                    output_file.write(f"{'='*80}\n\n")
                    output_file.write("Binary file or non-UTF-8 encoded text file, skipped.\n")
                except Exception as e:
                    output_file.write(f"\n\n{'='*80}\n")
                    output_file.write(f"File: {rel_path}\n")
                    output_file.write(f"{'='*80}\n\n")
                    output_file.write(f"Error reading file: {str(e)}\n")
        
        print(f"Repository content has been successfully saved to {output_file_path}")
    
    finally:
        # Clean up: remove the temporary directory
        print(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
