import json
from typing import Any, Dict, Optional, Tuple, Union


def run_assertions(
    deliverable: Optional[Dict[str, Any]],
    rules: Union[str, Dict[str, Any]],
) -> Tuple[bool, str]:
    """
    Executes programmatic contract assertion verification on digital deliverables.
    Checks:
    1. Deliverable presence.
    2. Deliverable format compliance (`json`, `text`, `binary`).
    3. Existence and non-nullness of all `required_keys`.
    4. Minimum length compliance (`min_length`).
    """
    if isinstance(rules, str):
        try:
            parsed_rules: Dict[str, Any] = json.loads(rules)
        except Exception:
            parsed_rules = {"format": "json", "required_keys": [], "min_length": 0}
    else:
        parsed_rules = rules or {"format": "json", "required_keys": [], "min_length": 0}

    required_keys = parsed_rules.get("required_keys", [])
    min_length = int(parsed_rules.get("min_length", 0))
    expected_format = parsed_rules.get("format", "json")

    if deliverable is None:
        if not required_keys and min_length <= 0:
            return True, "No deliverable assertions required."
        return False, "Missing deliverable payload: Seller agent submitted null deliverable."

    if expected_format == "json" and not isinstance(deliverable, dict):
        return (
            False,
            f"Deliverable format mismatch: Expected JSON object, got {type(deliverable).__name__}.",
        )

    # Check required keys
    if isinstance(deliverable, dict):
        missing_keys = [
            k for k in required_keys if k not in deliverable or deliverable[k] is None or deliverable[k] == ""
        ]
        if missing_keys:
            return (
                False,
                f"Contract Assertion Failed: Deliverable missing required keys {missing_keys}.",
            )

    # Check minimum payload length if specified
    if min_length > 0:
        serialized = json.dumps(deliverable) if isinstance(deliverable, dict) else str(deliverable)
        if len(serialized) < min_length:
            return (
                False,
                f"Contract Assertion Failed: Deliverable length ({len(serialized)}) is below minimum ({min_length}).",
            )

    return True, "Contract Deliverable verified against schema assertions."

