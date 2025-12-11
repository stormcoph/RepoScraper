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
    excluded_extensions = {
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.webp',
        '.dll', '.exe', '.bin', '.so', '.dylib',
        '.onnx', '.tensorrt', '.pt', '.pth', '.h5', '.pb',
        '.zip', '.tar', '.gz', '.xz', '.7z', '.rar',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
        '.db', '.sqlite', '.dat', 'hex'
    }

    if any(file_path.lower().endswith(ext) for ext in excluded_extensions):
        return True

    mime, _ = mimetypes.guess_type(file_path)
    if mime is None:
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except:
            return True

    text_mimes = ['text/', 'application/json', 'application/xml', 'application/javascript',
                  'application/x-python', 'application/x-ruby', 'application/x-php']

    return not any(text_type in mime for text_type in text_mimes)


def get_file_info(file_path):
    stat = os.stat(file_path)
    size = stat.st_size
    modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = sum(1 for _ in f)
    except:
        lines = "N/A"

    return {
        'size': size,
        'modified': modified,
        'lines': lines
    }


def ask_for_exclusions(valid_files):
    if not valid_files:
        return valid_files  # nothing to exclude

    choice = input("\nDo you want to exclude any files? (y/n): ").strip().lower()
    if choice != "y":
        return valid_files

    print("\nList of files (largest → smallest):\n")

    # Sort by size descending
    sorted_files = sorted(valid_files, key=lambda x: x['size'], reverse=True)

    # Print list in the requested format
    for idx, info in enumerate(sorted_files):
        size_kb = info['size'] / 1024
        size_str = f"{size_kb:.2f} KB"
        print(f"[{idx}] {info['path']} {size_str}")

    exclude_input = input(
        "\nEnter numbers of files to exclude (space-separated), or press Enter for none:\n> "
    ).strip()

    if not exclude_input:
        return sorted_files

    try:
        exclude_indices = {int(x) for x in exclude_input.split()}
    except ValueError:
        print("Invalid input. No exclusions applied.")
        return sorted_files

    filtered_list = [
        f for idx, f in enumerate(sorted_files)
        if idx not in exclude_indices
    ]

    print(f"\nExcluding {len(sorted_files) - len(filtered_list)} file(s).")
    return filtered_list


def process_directory(directory_path, output_file_name, source_info, script_to_exclude=None):
    print(f"Processing directory: {directory_path}")

    output_file_path = f"{output_file_name}_content.txt"
    MAX_FILE_SIZE = 10 * 1024 * 1024

    print("Collecting files...")
    valid_files = []

    for root, dirs, files in os.walk(directory_path):
        if '.git' in dirs:
            dirs.remove('.git')

        for file in files:
            file_path = os.path.join(root, file)

            if script_to_exclude and os.path.abspath(file_path) == script_to_exclude:
                print(f"Skipping the script itself: {os.path.relpath(file_path, directory_path)}")
                continue

            rel_path = os.path.relpath(file_path, directory_path)

            if is_binary_file(file_path):
                print(f"Skipping binary file: {rel_path}")
                continue

            try:
                size = os.path.getsize(file_path)
                if size > MAX_FILE_SIZE:
                    print(f"Skipping large file: {rel_path} ({size / 1024 / 1024:.2f} MB)")
                    continue

                valid_files.append({
                    'path': rel_path,
                    'size': size
                })
            except Exception as e:
                print(f"Error accessing file {rel_path}: {str(e)}")

    # Exclusion step (only option A files)
    valid_files = ask_for_exclusions(valid_files)

    # Sort final file list alphabetically for output
    valid_files.sort(key=lambda x: x['path'])

    print(f"\nWriting content to {output_file_path}...")
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(f"# Source: {source_info}\n")
        output_file.write(f"# Generated on: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        output_file.write("## Table of Contents\n\n")
        for i, info in enumerate(valid_files, 1):
            size_kb = info['size'] / 1024
            output_file.write(f"{i}. {info['path']} ({size_kb:.2f} KB)\n")

        for info in valid_files:
            rel_path = info['path']
            file_path = os.path.join(directory_path, rel_path)

            try:
                additional_info = get_file_info(file_path)

                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

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
                output_file.write("Binary or invalid text encoding - skipped.\n")
            except Exception as e:
                output_file.write(f"\n\n{'='*80}\n")
                output_file.write(f"File: {rel_path}\n")
                output_file.write(f"{'='*80}\n\n")
                output_file.write(f"Error reading file: {str(e)}\n")

    print(f"Content has been successfully saved to {output_file_path}")


def scrape_git_repository():
    repo_url = input("Enter the GitHub repository URL: ")

    if 'github.com' in repo_url and not repo_url.endswith('.git'):
        repo_url = repo_url + '.git'

    if not re.match(r'https?://github\.com/[^/]+/[^/]+/?.*', repo_url):
        print("Error: Invalid GitHub repository URL")
        sys.exit(1)

    repo_name = repo_url.split('/')[-1]
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]

    temp_dir = tempfile.mkdtemp()
    print(f"Using temporary directory: {temp_dir}")

    try:
        print(f"Cloning repository {repo_url}...")
        try:
            result = subprocess.run(
                ['git', 'clone', repo_url, temp_dir],
                stderr=subprocess.PIPE, stdout=subprocess.PIPE,
                universal_newlines=True
            )
            if result.returncode != 0:
                print(f"Error cloning repository: {result.stderr}")
                sys.exit(1)
        except Exception as e:
            print(f"Failed to execute git clone: {str(e)}")
            sys.exit(1)

        process_directory(temp_dir, repo_name, repo_url)

    finally:
        print(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)


def scrape_local_directory():
    print("\nSelect the local directory option:")
    print("1. Scrape current folder")
    print("2. Scrape a specified folder")
    local_choice = input("Enter your choice (1 or 2): ")

    if local_choice == '1':
        directory_path = os.getcwd()
    elif local_choice == '2':
        directory_path = input("Enter the path to the directory: ").strip()
        if not os.path.isdir(directory_path):
            print("Error: Invalid directory path.")
            sys.exit(1)
    else:
        print("Invalid choice. Please enter 1 or 2.")
        sys.exit(1)

    script_to_exclude = os.path.abspath(__file__)
    folder_name = os.path.basename(directory_path)
    process_directory(directory_path, folder_name, directory_path, script_to_exclude)


def main():
    print("Select the source to scrape from:")
    print("1. Git repository")
    print("2. Local directory")
    choice = input("Enter your choice (1 or 2): ")

    if choice == '1':
        scrape_git_repository()
    elif choice == '2':
        scrape_local_directory()
    else:
        print("Invalid choice. Please enter 1 or 2.")
        sys.exit(1)


if __name__ == "__main__":
    main()
