import re
import json
from pathlib import Path
from typing import Dict, Any
from components.extractor.formats.dynamic_format import DynamicFormat

class DocumentParser:
    def __init__(self):
        # Register available formats dynamically from the configs folder
        self.formats = []
        self._load_configs()

    def _load_configs(self):
        base_dir = Path(__file__).parent.parent
        configs_dir = base_dir / "configs"
        
        if not configs_dir.exists():
            configs_dir.mkdir(parents=True)
            return
            
        for config_file in configs_dir.glob("*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.formats.append(DynamicFormat(config_data))
            except Exception as e:
                print(f"Error loading configuration from {config_file.name}: {e}")

    def _split_pages(self, text: str) -> list[str]:
        # Split by form feed character (common in OCR for page breaks)
        pages = re.split(r'\x0c', text)
        return [p.strip() for p in pages if p.strip()]

    def parse(self, text: str) -> Dict[str, Any]:
        pages = self._split_pages(text)
        if not pages:
            return {"error": "Empty document"}

        first_page = pages[0]
        selected_format = None

        # 1. Identify format
        for fmt in self.formats:
            if fmt.is_match(first_page):
                selected_format = fmt
                break

        if not selected_format:
            return {"error": "El formato de este documento aún no ha sido configurado. Por favor agregue el archivo JSON de configuración en la carpeta configs/."}

        # 2. Extract Header (from first page)
        extracted_data = {
            "format": selected_format.format_name,
            "header": selected_format.extract_header_fields(first_page),
            "pages": [],
            "all_line_items": []
        }

        # 3. Extract Line Items per page
        for page_num, page_text in enumerate(pages, start=1):
            page_items = selected_format.extract_line_items(page_text)
            extracted_data["pages"].append({
                "page_number": page_num,
                "line_items_count": len(page_items),
                "line_items": page_items
            })
            extracted_data["all_line_items"].extend(page_items)

        return extracted_data
