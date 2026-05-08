import os

def get_output_dir():
    """
    Returns the absolute path to the 'components/ocr/output' directory.
    """
    base_dir = os.path.dirname(__file__)
    output_dir = os.path.join(base_dir, 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def check_if_processed(document_path):
    """
    Checks if a document has already been processed by looking for its output folder
    and .txt file in the components/ocr/output/ directory.
    Returns the output path if it exists, otherwise False.
    """
    base_name = os.path.splitext(os.path.basename(document_path))[0]
    output_dir = get_output_dir()
    doc_output_dir = os.path.join(output_dir, base_name)
    
    expected_file = os.path.join(doc_output_dir, f"{base_name}.txt")
    
    if os.path.exists(expected_file):
        return expected_file
    return False

def save_ocr_result(content, document_path):
    """
    Saves the OCR text result into components/ocr/output/<doc_name>/<doc_name>.txt
    """
    base_name = os.path.splitext(os.path.basename(document_path))[0]
    output_dir = get_output_dir()
    doc_output_dir = os.path.join(output_dir, base_name)
    
    if not os.path.exists(doc_output_dir):
        os.makedirs(doc_output_dir)
        
    output_file = os.path.join(doc_output_dir, f"{base_name}.txt")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
        
    return output_file
