import argparse
import os

from config import load_configuration
from ocr import VeryfiOCR
from file_utils import check_if_processed, save_ocr_result

def process_single_file(file_path, ocr_service):
    if not os.path.exists(file_path):
        print(f"Error: Document '{file_path}' does not exist.")
        return
        
    print(f"\nProcessing document: {file_path}")
    
    # Check if already processed
    existing_output = check_if_processed(file_path)
    if existing_output:
        print(f"Document already processed. Output exists at: {existing_output}")
        return
        
    try:
        # Call API
        ocr_text = ocr_service.extract_ocr_text(file_path)
        
        if ocr_text:
            output_path = save_ocr_result(ocr_text, file_path)
            print(f"OCR text successfully extracted and saved to: {output_path}")
        else:
            print(f"No OCR text found in the response for {file_path}.")
            
    except Exception as e:
        print(f"Error processing document {file_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Process a document using Veryfi OCR")
    parser.add_argument('file', nargs='?', help="Path to the document to process (e.g., documents/file.pdf)")
    args = parser.parse_args()
    
    # 1. Load Configuration
    try:
        config = load_configuration()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return

    # 2. Initialize OCR Service
    try:
        ocr_service = VeryfiOCR(config)
    except Exception as e:
        print(f"Failed to initialize OCR service: {e}")
        return

    # 3. Handle Execution
    if args.file:
        process_single_file(args.file, ocr_service)
    else:
        print("No file provided. Please provide a path to a document.")
        print("Usage: python components/ocr/main.py <path_to_document>")

if __name__ == '__main__':
    main()
