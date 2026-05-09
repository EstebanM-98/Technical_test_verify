import os
from pathlib import Path

from components.extractor.core.document_parser import DocumentParser
from components.extractor.utils.file_handler import read_text, write_json
from logger import get_logger

logger = get_logger(__name__, "extractor.log")


def extract_information(input_source: str, output_dir: str = None) -> dict:
    """
    Main entry point for the extractor.
    Receives either a file path to a .txt or raw text.

    Args:
        input_source: Absolute/relative path to a .txt file, or raw OCR text.
        output_dir:   Directory to save the JSON output. Defaults to
                      components/extractor/output/.

    Returns:
        Dictionary with extracted structured data, or {'error': ...} on failure.
    """
    # Determine input type and load text
    if os.path.isfile(input_source):
        logger.info("Input source is a file: '%s'", input_source)
        text = read_text(input_source)
        file_name = Path(input_source).stem
        logger.debug("File '%s' read: %d characters.", file_name, len(text))
    else:
        logger.info("Input source is raw text (%d characters).", len(input_source))
        text = input_source
        file_name = "extracted_document"

    # Resolve output directory
    if output_dir is None:
        base_dir = Path(__file__).parent
        output_dir = base_dir / "output"
    logger.debug("Output directory resolved to: '%s'", output_dir)

    # Parse
    parser = DocumentParser()
    logger.debug("Starting document parsing for '%s'.", file_name)
    extracted_data = parser.parse(text)

    if "error" in extracted_data:
        logger.error("Extraction failed for '%s': %s", file_name, extracted_data["error"])
        return extracted_data

    # Save output
    doc_output_dir = Path(output_dir) / file_name
    doc_output_dir.mkdir(parents=True, exist_ok=True)
    output_file = doc_output_dir / f"{file_name}.json"

    write_json(extracted_data, str(output_file))
    logger.info(
        "Extraction completed for '%s'. Results saved to: '%s'.", file_name, output_file
    )
    return extracted_data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract structured data from OCR text.")
    parser.add_argument("input", help="Path to the txt file or raw text.")
    parser.add_argument("--output", help="Path to output directory.", default=None)
    args = parser.parse_args()

    extract_information(args.input, args.output)
