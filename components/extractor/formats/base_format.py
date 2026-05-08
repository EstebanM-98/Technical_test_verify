from abc import ABC, abstractmethod
import re
from typing import List, Dict, Any

class BaseFormat(ABC):
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Name of the format"""
        pass

    @abstractmethod
    def is_match(self, first_page_text: str) -> bool:
        """Returns True if the document matches this format based on a signature regex."""
        pass

    @abstractmethod
    def extract_header_fields(self, page_text: str) -> Dict[str, Any]:
        """Extracts localized fields like vendor name, date, invoice number from the text."""
        pass

    @abstractmethod
    def extract_line_items(self, page_text: str) -> List[Dict[str, Any]]:
        """Robustly extracts line items (movimientos) from the page."""
        pass
