#!/usr/bin/env python3
import json
import argparse
import os
import sys

# --- Defaults ---
# These are removed by default unless flags are used
MIME_STATIC = {
    'image/', 'audio/', 'video/', 'font/', 'application/font',
    'application/woff', 'application/x-font'
}
EXT_STATIC = {
    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', 
    '.woff', '.woff2', '.ttf', '.eot', '.mp4', '.mp3'
}

MIME_CSS = {'text/css'}
EXT_CSS = {'.css', '.map'}

def clean_har(input_path, output_path, args):
    """Main processing logic."""
    print(f"[*] Processing: {input_path}")

    # Load JSON (Robust to .har or .txt extensions)
    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("[!] Error: File is not valid JSON.")
        sys.exit(1)
    except Exception as e:
        print(f"[!] File error: {e}")
        sys.exit(1)

    # Validate HAR structure
    if 'log' not in data or 'entries' not in data['log']:
        print("[!] Error: JSON structure does not match HAR format.")
        sys.exit(1)

    entries = data['log']['entries']
    original_count = len(entries)
    cleaned_entries = []

    # Prepare filter lists based on arguments
    blocked_mimes = set()
    blocked_exts = set()

    # 1. Logic: If we are NOT keeping static assets, block them
    if not args.keep_static:
        blocked_mimes.update(MIME_STATIC)
        blocked_exts.update(EXT_STATIC)

    # 2. Logic: If we are NOT keeping CSS, block it
    if not args.keep_css:
        blocked_mimes.update(MIME_CSS)
        blocked_exts.update(EXT_CSS)

    for entry in entries:
        req = entry.get('request', {})
        res = entry.get('response', {})
        
        # --- Check 1: Filter by Content Type (MIME) ---
        mime = res.get('content', {}).get('mimeType', '').lower()
        if any(b in mime for b in blocked_mimes):
            continue

        # --- Check 2: Filter by URL Extension ---
        url = req.get('url', '').lower().split('?')[0] # Ignore query params
        if any(url.endswith(ext) for ext in blocked_exts):
            continue

        # --- Cleaning: Strip Metadata (Always done to reduce noise) ---
        # Timings and Cache are rarely useful for logic vulnerability scanning
        for key in ['timings', 'cache', 'pageref', 'time', '_initiator', '_priority']:
            if key in entry:
                del entry[key]

        # --- Cleaning: Handle Binary Response Data ---
        # We need text for analysis, but base64 blobs kill token limits.
        if 'content' in res:
            content = res['content']
            if 'text' in content and content.get('encoding') == 'base64':
                # If user specifically wants binary, we keep it, otherwise strip
                if not args.keep_binary:
                    content['text'] = "[BINARY_DATA_REMOVED]"

        cleaned_entries.append(entry)

    # Reconstruct data
    data['log']['entries'] = cleaned_entries
    
    # Optional: Clean browser metadata
    if 'pages' in data['log']: del data['log']['pages']
    data['log']['browser'] = {"name": "HAR Cleaner Tool", "version": "2.0"}

    # Stats
    removed = original_count - len(cleaned_entries)
    print(f"    - Original: {original_count} requests")
    print(f"    - Removed:  {removed} (Bloat)")
    print(f"    - Final:    {len(cleaned_entries)} requests")

    # Save
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print(f"[*] Success! Saved to: {output_path}")
    except Exception as e:
        print(f"[!] Write error: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Clean HAR files for AI Security Analysis.",
        epilog="Example: harclean capture.har --keep-css"
    )
    
    # Positional Argument (Input file)
    parser.add_argument("input", help="The .har or .txt file to clean.")
    
    # Optional Argument (Output file)
    parser.add_argument("-o", "--output", help="Output filename. Defaults to <input>_clean.json")

    # Boolean Flags (Switches)
    parser.add_argument("--keep-css", action="store_true", help="Don't remove CSS files.")
    parser.add_argument("--keep-static", action="store_true", help="Don't remove Images, Fonts, Icons, etc.")
    parser.add_argument("--keep-binary", action="store_true", help="Don't strip base64 binary response data.")

    args = parser.parse_args()

    # Determine Output Filename
    if args.output:
        out_path = args.output
    else:
        base, _ = os.path.splitext(args.input)
        out_path = f"{base}_clean.json"

    clean_har(args.input, out_path, args)

if __name__ == "__main__":
    main()