import sys
import os
from pathlib import Path

# Add project root to sys.path to allow importing from components
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from components.ocr.main import process_single_file
from components.ocr.config import load_configuration
from components.ocr.ocr import VeryfiOCR
from components.extractor.main import extract_information

def process_document_pipeline(pdf_path: str):
    """
    Orchestrates the pipeline: PDF -> OCR -> Extractor
    """
    print(f"--- Iniciando Pipeline para: {pdf_path} ---")
    
    # 1. Ejecutar OCR
    print("\n[Paso 1] Ejecutando OCR...")
    try:
        config = load_configuration()
        ocr_service = VeryfiOCR(config)
    except Exception as e:
        print(f"[ERROR] Falló la inicialización del OCR: {e}")
        return
        
    txt_output_path = process_single_file(pdf_path, ocr_service)
    
    if not txt_output_path:
        print("[ERROR] El proceso de OCR falló o no generó un archivo de texto.")
        return
        
    print(f"[OK] Texto OCR obtenido en: {txt_output_path}")

    # 2. Ejecutar Extractor
    print("\n[Paso 2] Ejecutando Extractor de Datos (JSON)...")
    try:
        json_data = extract_information(txt_output_path)
        if "error" not in json_data:
            print("[OK] Datos estructurados correctamente.")
    except Exception as e:
        print(f"[ERROR] Falló la extracción de datos: {e}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Pipeline completo de extracción bancaria")
    parser.add_argument("file", help="Ruta al documento PDF original (ej: documents/synth-switch_v5-79.pdf)")
    args = parser.parse_args()
    
    process_document_pipeline(args.file)
