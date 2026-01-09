#!/usr/bin/env python3
import json
import argparse
import sys
import os

def recursive_replace(obj, secret, replacement):
    """Recursively traverses JSON to replace text within strings."""
    if isinstance(obj, dict):
        return {k: recursive_replace(v, secret, replacement) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [recursive_replace(i, secret, replacement) for i in obj]
    elif isinstance(obj, str):
        if secret in obj:
            return obj.replace(secret, replacement)
    return obj

def recursive_delete_key(obj, secret):
    """Recursively traverses JSON to delete any Key/Value pair containing the secret."""
    if isinstance(obj, dict):
        clean_dict = {}
        for k, v in obj.items():
            # Check if secret is in the value (string representation)
            if isinstance(v, str) and secret in v:
                continue # Skip this key (Delete line)
            # Check if secret is in the key itself
            if secret in k:
                continue
            
            clean_value = recursive_delete_key(v, secret)
            # If the value became empty because everything inside was deleted, we keep the empty container
            clean_dict[k] = clean_value
        return clean_dict
    elif isinstance(obj, list):
        # Filter out items in a list that contain the secret
        return [recursive_delete_key(i, secret) for i in obj if not (isinstance(i, str) and secret in i)]
    return obj

def process_file(args):
    filepath = args.input_file
    secret = args.secret
    
    print(f"[*] Reading: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[!] Error: Could not read JSON. {e}")
        sys.exit(1)

    # 1. DELETE ENTIRE REQUEST (Entry)
    if args.action == 'delete-req':
        if 'log' in data and 'entries' in data['log']:
            original_len = len(data['log']['entries'])
            # Filter entries. Convert entry to string to check for secret existence easily.
            data['log']['entries'] = [
                entry for entry in data['log']['entries'] 
                if secret not in json.dumps(entry)
            ]
            new_len = len(data['log']['entries'])
            print(f"[*] Removed {original_len - new_len} full requests containing the secret.")
        else:
            print("[!] Warning: File structure doesn't look like a standard HAR.")

    # 2. DELETE LINE (Key/Value pair)
    elif args.action == 'delete-line':
        data = recursive_delete_key(data, secret)
        print(f"[*] Removed all JSON keys/lines containing the secret.")

    # 3. REPLACE TEXT (Redact)
    elif args.action == 'replace':
        replacement = args.text if args.text else "[REDACTED]"
        data = recursive_replace(data, secret, replacement)
        print(f"[*] Replaced instances of secret with '{replacement}'.")

    # Output
    output_path = args.output if args.output else f"{os.path.splitext(filepath)[0]}_redacted.json"
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"[*] Saved to: {output_path}")
    except Exception as e:
        print(f"[!] Error saving file: {e}")

def main():
    parser = argparse.ArgumentParser(description="Simple HAR Redactor")
    
    parser.add_argument("input_file", help="Path to .har or .txt file")
    parser.add_argument("secret", help="The specific text/token you want to find")
    
    # Action Group (User must pick one)
    group = parser.add_argument_group('Actions')
    exclusive = group.add_mutually_exclusive_group(required=True)
    exclusive.add_argument("--replace", action="store_const", const="replace", dest="action", 
                           help="Replace the secret with text (default: [REDACTED])")
    exclusive.add_argument("--delete-line", action="store_const", const="delete-line", dest="action", 
                           help="Delete the specific JSON key/line containing the secret")
    exclusive.add_argument("--delete-req", action="store_const", const="delete-req", dest="action", 
                           help="Delete the entire Request/Response block containing the secret")

    parser.add_argument("--text", help="Custom replacement text (used with --replace)")
    parser.add_argument("-o", "--output", help="Output file path")

    args = parser.parse_args()
    process_file(args)

if __name__ == "__main__":
    main()