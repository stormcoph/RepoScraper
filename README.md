# AI Security & Analysis Toolkit

A set of lightweight, standard-library Python scripts designed to prepare data (codebases and network traffic) for AI analysis and security auditing.

**Prerequisites:** Python 3.x (No external libraries required).

## 1. Code Scraper (`scraper.py`)
Consolidates an entire Git repository or local directory into a single `.txt` file. Ideal for feeding context to LLMs.

**Features:**
*   Automatically filters binaries and large files.
*   Interactive prompt to exclude specific files by size.
*   Supports GitHub URLs or local paths.

**Usage:**
```bash
python3 scraper.py
# Follow the interactive prompts to select source and exclusions.
```

---

## 2. HAR Cleaner (`harcleaner.py`)
Optimizes HAR (network log) files for AI analysis by removing "bloat" (images, fonts, binary blobs) to save tokens while preserving request logic.

**Usage:**

*   **Default (Best for Logic Analysis):** Removes static assets, binary data, and timing metadata.
    ```bash
    python3 harcleaner.py traffic.har
    ```

*   **Keep CSS (For UI Analysis):**
    ```bash
    python3 harcleaner.py traffic.har --keep-css
    ```

*   **Keep Everything (Just remove metadata):**
    ```bash
    python3 harcleaner.py traffic.har --keep-static --keep-css --keep-binary
    ```

---

## 3. HAR Redactor (`har_redact.py`)
Surgically removes or replaces specific secrets (tokens, passwords, API keys) from HAR files without breaking the JSON structure.

**Usage:**

*   **Replace Secret:** Finds the token and replaces it with `[REDACTED]`.
    ```bash
    python3 har_redact.py traffic.har "MY_SECRET_TOKEN" --replace
    ```

*   **Delete Line:** Removes the specific JSON key/value pair containing the secret.
    ```bash
    python3 har_redact.py traffic.har "MY_SECRET_TOKEN" --delete-line
    ```

*   **Delete Request:** Removes the entire HTTP request/response entry if the secret is found anywhere inside it.
    ```bash
    python3 har_redact.py traffic.har "MY_SECRET_TOKEN" --delete-req
    ```

---

## Quick Setup (Optional)
Make scripts executable to run them directly from your terminal:

```bash
chmod +x scraper.py harcleaner.py har_redact.py
```
Now you can run them as `./scraper.py`, etc.
