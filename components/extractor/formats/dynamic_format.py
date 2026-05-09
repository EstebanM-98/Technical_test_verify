import re
from typing import Any, Dict, List

from .base_format import BaseFormat
from logger import get_logger

logger = get_logger(__name__, "extractor.log")


class DynamicFormat(BaseFormat):
    """
    A dynamic format parser that builds its extraction rules from a JSON
    configuration file. Supports regex-based header extraction and
    anchor-delimited line-item table parsing.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._format_name = config.get("format_name", "Unknown")
        self.signature_regex = config.get("signature_regex", "")
        self.header_rules = config.get("header_fields", {})
        self.line_item_rules = config.get("line_items", {})
        logger.debug("DynamicFormat '%s' created.", self._format_name)

    @property
    def format_name(self) -> str:
        return self._format_name

    def is_match(self, first_page_text: str) -> bool:
        """Returns True if the document's first page matches this format's signature."""
        if not self.signature_regex:
            logger.debug("Format '%s' has no signature_regex; skipping match.", self._format_name)
            return False
        matched = bool(re.search(self.signature_regex, first_page_text))
        logger.debug("Format '%s' match result: %s.", self._format_name, matched)
        return matched

    def extract_header_fields(self, page_text: str) -> Dict[str, Any]:
        """Extracts header fields using the configured regex and static rules."""
        data: Dict[str, Any] = {}
        for field, rule in self.header_rules.items():
            if rule.get("type") == "static":
                data[field] = rule.get("value")
            elif rule.get("type") == "regex":
                pattern = rule.get("pattern")
                group = rule.get("group", 1)
                match = re.search(pattern, page_text)
                if match:
                    data[field] = match.group(group).strip()
                else:
                    data[field] = None
                    logger.debug(
                        "Header field '%s' not matched in document (pattern: %s).",
                        field, pattern,
                    )
        logger.debug(
            "Header extraction complete for format '%s': %d/%d fields populated.",
            self._format_name,
            sum(1 for v in data.values() if v is not None),
            len(data),
        )
        return data

    def extract_line_items(self, page_text: str) -> List[Dict[str, Any]]:
        """
        Extracts line items from a single page using anchor-based table detection
        and a row regex pattern defined in the configuration.
        """
        line_items: List[Dict[str, Any]] = []
        if not self.line_item_rules:
            logger.debug("No line_item_rules defined for format '%s'.", self._format_name)
            return line_items

        start_anchor = self.line_item_rules.get("start_anchor")
        stop_anchor = self.line_item_rules.get("stop_anchor")
        row_pattern = re.compile(self.line_item_rules.get("row_pattern", ""))
        columns = self.line_item_rules.get("columns", [])

        in_table = False
        lines = page_text.split("\n")
        current_item: Dict[str, Any] | None = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for table start
            if start_anchor and re.search(start_anchor, line):
                in_table = True
                logger.debug("Table start anchor matched: '%s'.", line)
                continue

            if in_table:
                # Check for table end
                if stop_anchor and re.search(stop_anchor, line):
                    logger.debug("Table stop anchor matched: '%s'.", line)
                    break

                match = row_pattern.match(line)
                if match:
                    if current_item:
                        line_items.append(current_item)

                    current_item = {}
                    for i, col in enumerate(columns, start=1):
                        val = match.group(i).strip()
                        if col in ("quantity", "rate", "amount"):
                            val = float(val.replace(",", "")) if val else 0.0
                        current_item[col] = val
                elif current_item:
                    # Overflow line — append to first column (description)
                    first_col = columns[0]
                    current_item[first_col] += " " + line

        # Append last item
        if current_item:
            line_items.append(current_item)

        logger.debug(
            "Line item extraction complete for format '%s': %d item(s) found.",
            self._format_name, len(line_items),
        )
        return line_items
