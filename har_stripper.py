import sys
import os

def strip_har_file(input_path):
    # Check if the file exists
    if not os.path.isfile(input_path):
        print(f"Error: File '{input_path}' not found.")
        return

    # Extract the filename and extension
    base_name, ext = os.path.splitext(input_path)
    output_path = f"{base_name}_stripped{ext}"

    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as infile, \
             open(output_path, 'w', encoding='utf-8') as outfile:
            
            for line in infile:
                # Only write lines that are 1000 characters or shorter
                if len(line) <= 1000:
                    outfile.write(line)
        
        print(f"Successfully processed. Output saved to: {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Ensure a filename was provided as an argument
    if len(sys.argv) != 2:
        print("Usage: python3 har_stripper.py {filename}.har")
    else:
        strip_har_file(sys.argv[1])