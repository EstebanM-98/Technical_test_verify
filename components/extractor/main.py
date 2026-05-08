import os
import json
from pathlib import Path
from components.extractor.core.document_parser import DocumentParser
from components.extractor.utils.file_handler import read_text, write_json

def extract_information(input_source: str, output_dir: str = None) -> dict:
    """
    Main entry point for the extractor.
    Receives either a file path to a .txt or raw text.
    """
    if os.path.isfile(input_source):
        text = read_text(input_source)
        file_name = Path(input_source).stem
    else:
        text = input_source
        file_name = "extracted_document"

    if output_dir is None:
        # Default output inside components/extractor/output
        base_dir = Path(__file__).parent
        output_dir = base_dir / "output"
    
    # Initialize parser and extract data
    parser = DocumentParser()
    extracted_data = parser.parse(text)
    
    if "error" in extracted_data:
        print(f"\n[ERROR] La extracción falló para '{file_name}': {extracted_data['error']}\n")
        return extracted_data
    
    # Save output
    doc_output_dir = Path(output_dir) / file_name
    doc_output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = doc_output_dir / f"{file_name}.json"
    write_json(extracted_data, str(output_file))
    
    print(f"Extraction completed. Results saved to: {output_file}")
    return extracted_data

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Extract structured data from OCR text.")
    parser.add_argument("input", help="Path to the txt file or raw text.")
    parser.add_argument("--output", help="Path to output directory.", default=None)
    args = parser.parse_args()
    
    extract_information(args.input, args.output)
