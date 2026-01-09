#!/usr/bin/env python3
import json
import argparse
import sys
import os

def filter_har(input_path, output_path, keywords, ignore_case):
    print(f"[*] Reading: {input_path}")
    
    # 1. Load the File
    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("[!] Error: File is not valid JSON.")
        sys.exit(1)
    except Exception as e:
        print(f"[!] File error: {e}")
        sys.exit(1)

    # 2. Validate HAR Structure
    if 'log' not in data or 'entries' not in data['log']:
        print("[!] Error: JSON does not look like a standard HAR file.")
        sys.exit(1)

    entries = data['log']['entries']
    original_count = len(entries)
    kept_entries = []

    # 3. Filter Logic
    print(f"[*] Searching for inclusions: {keywords}")
    
    # Pre-process keywords for case-insensitivity if requested
    search_terms = [k.lower() for k in keywords] if ignore_case else keywords

    for entry in entries:
        # Convert the specific entry to a string to search everything 
        # (Headers, URL, Response Body, Request Body, etc.)
        entry_str = json.dumps(entry)
        
        if ignore_case:
            entry_str = entry_str.lower()

        # INCLUSION LOGIC: Keep if ANY keyword is found
        if any(term in entry_str for term in search_terms):
            kept_entries.append(entry)

    # 4. Save Result
    data['log']['entries'] = kept_entries
    
    print(f"    - Original: {original_count}")
    print(f"    - Kept:     {len(kept_entries)}")
    print(f"    - Removed:  {original_count - len(kept_entries)}")

    if len(kept_entries) == 0:
        print("[!] Warning: No requests matched your keywords. Output file will be empty of entries.")

    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"[*] Saved to: {output_path}")
    except Exception as e:
        print(f"[!] Write error: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="HAR Inclusion Filter: Only keep requests containing specific strings."
    )
    
    parser.add_argument("input_file", help="Path to the .har or .txt file")
    parser.add_argument("keywords", nargs='+', help="List of strings to search for (e.g., 'api/v9' 'json')")
    parser.add_argument("-o", "--output", help="Output file path (optional)")
    parser.add_argument("-i", "--ignore-case", action="store_true", help="Perform case-insensitive matching")

    args = parser.parse_args()

    # Determine output filename if not provided
    if args.output:
        out_path = args.output
    else:
        base, _ = os.path.splitext(args.input_file)
        out_path = f"{base}_filtered.json"

    filter_har(args.input_file, out_path, args.keywords, args.ignore_case)

if __name__ == "__main__":
    main()