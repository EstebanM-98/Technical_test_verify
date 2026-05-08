import re
from typing import List, Dict, Any
from .base_format import BaseFormat

class DynamicFormat(BaseFormat):
    """
    A dynamic format parser that builds its rules from a JSON configuration file.
    """
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._format_name = config.get("format_name", "Unknown")
        self.signature_regex = config.get("signature_regex", "")
        self.header_rules = config.get("header_fields", {})
        self.line_item_rules = config.get("line_items", {})
        
    @property
    def format_name(self) -> str:
        return self._format_name

    def is_match(self, first_page_text: str) -> bool:
        if not self.signature_regex:
            return False
        return bool(re.search(self.signature_regex, first_page_text))

    def extract_header_fields(self, page_text: str) -> Dict[str, Any]:
        data = {}
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
        return data

    def extract_line_items(self, page_text: str) -> List[Dict[str, Any]]:
        line_items = []
        if not self.line_item_rules:
            return line_items
            
        start_anchor = self.line_item_rules.get("start_anchor")
        stop_anchor = self.line_item_rules.get("stop_anchor")
        row_pattern = re.compile(self.line_item_rules.get("row_pattern", ""))
        columns = self.line_item_rules.get("columns", [])
        
        in_table = False
        lines = page_text.split('\n')
        current_item = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for table start
            if start_anchor and re.search(start_anchor, line):
                in_table = True
                continue
                
            if in_table:
                # Check for table end
                if stop_anchor and re.search(stop_anchor, line):
                    break
                    
                match = row_pattern.match(line)
                if match:
                    # Save the previous item if it exists
                    if current_item:
                        line_items.append(current_item)
                        
                    current_item = {}
                    for i, col in enumerate(columns, start=1):
                        val = match.group(i).strip()
                        if col in ["quantity", "rate", "amount"]:
                            # Convert to float
                            val = float(val.replace(',', '')) if val else 0.0
                        current_item[col] = val
                elif current_item:
                    # It's an overflow line of the description
                    first_col = columns[0]
                    current_item[first_col] += " " + line

        # Append the last item
        if current_item:
            line_items.append(current_item)
            
        return line_items
