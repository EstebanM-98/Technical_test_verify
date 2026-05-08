import json
from pathlib import Path

class ValidatorEngine:
    def __init__(self):
        self.configs = {}
        self._load_configs()

    def _load_configs(self):
        config_dir = Path(__file__).parent.parent / "configs"
        if not config_dir.exists():
            config_dir.mkdir(parents=True)
            return
            
        for config_file in config_dir.glob("*.json"):
            with open(config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                fmt_name = data.get("format_name")
                if fmt_name:
                    self.configs[fmt_name] = data

    def validate(self, extracted_data: dict) -> dict:
        fmt_name = extracted_data.get("format")
        if not fmt_name or fmt_name not in self.configs:
            return {"is_valid": False, "message": f"No validation config found for format '{fmt_name}'", "errors": []}
            
        config = self.configs[fmt_name]
        rules = config.get("rules", [])
        errors = []
        
        # We need to validate across all line items from all pages
        all_items = []
        for page in extracted_data.get("pages", []):
            all_items.extend(page.get("line_items", []))
            
        header = extracted_data.get("header", {})
        
        for rule in rules:
            if rule["type"] == "row_math":
                for idx, row in enumerate(all_items):
                    try:
                        q = float(str(row.get("quantity", 0)).replace(',', ''))
                        r = float(str(row.get("rate", 0)).replace(',', ''))
                        a = float(str(row.get("amount", 0)).replace(',', ''))
                        expected = q * r
                        if abs(expected - a) > rule.get("tolerance", 0.1):
                            errors.append(f"Row {idx+1} Math Error: Quantity ({q}) * Rate ({r}) != Amount ({a})")
                    except Exception as e:
                        errors.append(f"Row {idx+1} Math Evaluation Error: {e}")
                        
            elif rule["type"] == "document_sum":
                sum_col = rule["sum_column"]
                target_header = rule["equals_header"]
                
                try:
                    total_calculated = sum(float(str(row.get(sum_col, 0)).replace(',', '')) for row in all_items)
                    
                    target_val_str = header.get(target_header)
                    if not target_val_str:
                        errors.append(f"Header field '{target_header}' not found for sum check.")
                        continue
                        
                    target_val = float(str(target_val_str).replace(',', ''))
                    
                    if abs(total_calculated - target_val) > rule.get("tolerance", 0.1):
                        errors.append(f"Sum Error: Calculated sum of {sum_col} ({total_calculated}) != Header {target_header} ({target_val})")
                except Exception as e:
                    errors.append(f"Sum Evaluation Error: {e}")
                    
        is_valid = len(errors) == 0
        return {
            "is_valid": is_valid,
            "message": "Validated ✅" if is_valid else "Validation Failed",
            "errors": errors
        }
