import json
from pathlib import Path

from logger import get_logger

logger = get_logger(__name__, "validator.log")


class ValidatorEngine:
    def __init__(self):
        self.configs: dict = {}
        self._load_configs()

    def _load_configs(self):
        """Loads all JSON validation config files from the configs/ directory."""
        config_dir = Path(__file__).parent.parent / "configs"

        if not config_dir.exists():
            config_dir.mkdir(parents=True)
            logger.warning(
                "Validator configs directory did not exist and was created: '%s'. "
                "No validation rules are loaded.",
                config_dir,
            )
            return

        loaded = 0
        for config_file in config_dir.glob("*.json"):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                fmt_name = data.get("format_name")
                if fmt_name:
                    self.configs[fmt_name] = data
                    loaded += 1
                    rules_count = len(data.get("rules", []))
                    logger.debug(
                        "Loaded validator config: '%s' with %d rule(s).",
                        config_file.name, rules_count,
                    )
                else:
                    logger.warning(
                        "Skipping '%s': missing 'format_name' key.", config_file.name
                    )
            except Exception:
                logger.exception("Error loading validator config: '%s'.", config_file.name)

        logger.info(
            "ValidatorEngine initialized: %d format config(s) loaded.", loaded
        )

    def validate(self, extracted_data: dict) -> dict:
        """
        Validates extracted document data against the stored rules for its format.

        Returns a result dict with keys: is_valid, message, errors, details.
        """
        fmt_name = extracted_data.get("format")
        logger.debug("Running validation for format='%s'.", fmt_name)

        if not fmt_name or fmt_name not in self.configs:
            logger.warning(
                "No validation config found for format='%s'. Available: %s.",
                fmt_name, list(self.configs.keys()),
            )
            return {
                "is_valid": False,
                "message": f"No validation config found for format '{fmt_name}'",
                "errors": [],
            }

        config = self.configs[fmt_name]
        rules = config.get("rules", [])
        errors: list[str] = []
        details: list[dict] = []

        # Consolidate all line items across pages
        all_items: list[dict] = []
        for page in extracted_data.get("pages", []):
            all_items.extend(page.get("line_items", []))

        header = extracted_data.get("header", {})
        logger.debug(
            "Validating format='%s': %d rule(s), %d line item(s).",
            fmt_name, len(rules), len(all_items),
        )

        for rule in rules:
            rule_type = rule.get("type")
            logger.debug("Applying rule type='%s'.", rule_type)

            if rule_type == "row_math":
                self._apply_row_math(rule, all_items, errors, details)

            elif rule_type == "document_sum":
                self._apply_document_sum(rule, all_items, header, errors, details)

            else:
                logger.warning("Unknown rule type '%s' — skipping.", rule_type)

        is_valid = len(errors) == 0
        logger.info(
            "Validation complete for format='%s': is_valid=%s, errors=%d.",
            fmt_name, is_valid, len(errors),
        )
        return {
            "is_valid": is_valid,
            "message": "Validated ✅" if is_valid else "Validation Failed",
            "errors": errors,
            "details": details,
        }

    # ─── Private rule handlers ─────────────────────────────────────────────────

    def _apply_row_math(
        self,
        rule: dict,
        all_items: list,
        errors: list,
        details: list,
    ) -> None:
        """Validates quantity × rate == amount for each line item."""
        tolerance = rule.get("tolerance", 0.1)
        for idx, row in enumerate(all_items):
            try:
                q = float(str(row.get("quantity", 0)).replace(",", ""))
                r = float(str(row.get("rate", 0)).replace(",", ""))
                a = float(str(row.get("amount", 0)).replace(",", ""))
                expected = q * r
                if abs(expected - a) > tolerance:
                    msg = f"Row {idx + 1} Math Error: Quantity ({q}) * Rate ({r}) != Amount ({a})"
                    logger.debug(msg)
                    errors.append(msg)
                    details.append({"check": f"Row {idx + 1} Math", "status": False, "message": msg})
                else:
                    details.append({
                        "check": f"Row {idx + 1} Math",
                        "status": True,
                        "message": f"Row {idx + 1} valid: {q} * {r} == {a}",
                    })
            except Exception:
                msg = f"Row {idx + 1} Math Evaluation Error"
                logger.exception(msg)
                errors.append(msg)
                details.append({"check": f"Row {idx + 1} Math", "status": False, "message": msg})

    def _apply_document_sum(
        self,
        rule: dict,
        all_items: list,
        header: dict,
        errors: list,
        details: list,
    ) -> None:
        """Validates that the sum of a column matches a header field value."""
        sum_col = rule["sum_column"]
        target_header = rule["equals_header"]
        tolerance = rule.get("tolerance", 0.1)
        try:
            total_calculated = sum(
                float(str(row.get(sum_col, 0)).replace(",", "")) for row in all_items
            )
            target_val_str = header.get(target_header)
            if not target_val_str:
                msg = f"Header field '{target_header}' not found for sum check."
                logger.warning(msg)
                errors.append(msg)
                details.append({"check": "Document Sum", "status": False, "message": msg})
                return

            target_val = float(str(target_val_str).replace(",", ""))
            if abs(total_calculated - target_val) > tolerance:
                msg = (
                    f"Sum Error: Calculated sum of {sum_col} ({total_calculated}) "
                    f"!= Header {target_header} ({target_val})"
                )
                logger.warning(msg)
                errors.append(msg)
                details.append({"check": "Document Sum", "status": False, "message": msg})
            else:
                details.append({
                    "check": "Document Sum",
                    "status": True,
                    "message": f"Sum valid: {total_calculated} == {target_val}",
                })
        except Exception:
            msg = "Sum Evaluation Error"
            logger.exception(msg)
            errors.append(msg)
            details.append({"check": "Document Sum", "status": False, "message": msg})
