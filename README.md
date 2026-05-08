# Veryfi Python Project

This project demonstrates the usage of the [Veryfi Python SDK](https://github.com/veryfi/veryfi-python) following best practices for project structure.

## Project Structure

- `src/`: Contains the main application code (`main.py`).
- `documents/`: Folder intended to store sample documents (receipts, invoices) for processing.
- `.env`: Environment variables file (credentials).
- `requirements.txt`: Python dependencies.

## Setup Instructions

1. **Configure Environment Variables**
   Open the `.env` file and replace the placeholders with your actual Veryfi API credentials:
   - `VERYFI_CLIENT_ID`
   - `VERYFI_CLIENT_SECRET`
   - `VERYFI_USERNAME`
   - `VERYFI_API_KEY`

2. **Activate the Virtual Environment**
   - Windows:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```

3. **Install Dependencies**
   Install the required libraries using `pip`:
   ```powershell
   pip install -r requirements.txt
   ```

4. **Run the Application**
   Place an example image or PDF (e.g., `example_receipt.jpg`) inside the `documents/` folder.
   Then execute the main script:
   ```powershell
   python src/main.py
   ```
