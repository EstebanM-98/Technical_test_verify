import json
import re
from pathlib import Path
from typing import Any, Dict

from components.extractor.formats.dynamic_format import DynamicFormat
from logger import get_logger

logger = get_logger(__name__, "extractor.log")


class DocumentParser:
    def __init__(self):
        # Register available formats dynamically from the configs folder
        self.formats: list[DynamicFormat] = []
        self._load_configs()

    def _load_configs(self):
        """Loads all JSON format configuration files from the configs/ directory."""
        base_dir = Path(__file__).parent.parent
        configs_dir = base_dir / "configs"

        if not configs_dir.exists():
            configs_dir.mkdir(parents=True)
            logger.warning(
                "Configs directory did not exist and was created: '%s'. "
                "No formats are loaded.",
                configs_dir,
            )
            return

        loaded = 0
        for config_file in configs_dir.glob("*.json"):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                    self.formats.append(DynamicFormat(config_data))
                    loaded += 1
                    logger.debug("Loaded format config: '%s'", config_file.name)
            except Exception:
                logger.exception("Error loading configuration from '%s'.", config_file.name)

        logger.info("DocumentParser initialized: %d format(s) loaded.", loaded)

    def _split_pages(self, text: str) -> list[str]:
        """Splits document text into pages using the form feed character (\\x0c)."""
        pages = re.split(r"\x0c", text)
        return [p.strip() for p in pages if p.strip()]

    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parses the OCR text into a structured document dictionary.

        Returns a dict with keys: format, header, pages, all_line_items.
        Returns {'error': '<reason>'} if parsing cannot proceed.
        """
        pages = self._split_pages(text)
        logger.debug("Document split into %d page(s).", len(pages))

        if not pages:
            logger.warning("Document appears to be empty after splitting.")
            return {"error": "Empty document"}

        first_page = pages[0]
        selected_format = None

        # 1. Identify format
        for fmt in self.formats:
            if fmt.is_match(first_page):
                selected_format = fmt
                logger.info("Format identified: '%s'.", fmt.format_name)
                break

        if not selected_format:
            logger.warning(
                "No matching format found for this document. "
                "Available formats: %s",
                [f.format_name for f in self.formats],
            )
            return {
                "error": (
                    "El formato de este documento aún no ha sido configurado. "
                    "Por favor agregue el archivo JSON de configuración en la carpeta configs/."
                )
            }

        # 2. Extract header
        extracted_data: Dict[str, Any] = {
            "format": selected_format.format_name,
            "header": selected_format.extract_header_fields(text),
            "pages": [],
            "all_line_items": [],
        }
        logger.debug("Header extracted: %s", list(extracted_data["header"].keys()))

        # 3. Extract line items per page
        for page_num, page_text in enumerate(pages, start=1):
            page_items = selected_format.extract_line_items(page_text)
            extracted_data["pages"].append({
                "page_number": page_num,
                "line_items_count": len(page_items),
                "line_items": page_items,
            })
            extracted_data["all_line_items"].extend(page_items)
            logger.debug("Page %d: %d line item(s) extracted.", page_num, len(page_items))

        total_items = len(extracted_data["all_line_items"])
        logger.info(
            "Parsing complete: format='%s', pages=%d, total_line_items=%d.",
            selected_format.format_name, len(pages), total_items,
        )
        return extracted_data
