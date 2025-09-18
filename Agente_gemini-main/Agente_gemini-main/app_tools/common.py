import json
import os
from typing import Any, Dict, List, Optional


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CUSTOMERS_JSON_PATH = os.path.join(DATA_DIR, "customers.json")


def _load_json(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_customers() -> List[Dict[str, Any]]:
    data = _load_json(CUSTOMERS_JSON_PATH)
    customers = data.get("customers", [])
    if not isinstance(customers, list):
        raise ValueError("Invalid customers.json format: 'customers' must be a list")
    return customers


def find_customer(customer_id: str) -> Optional[Dict[str, Any]]:
    for c in load_customers():
        if c.get("customer_id") == customer_id:
            return c
    return None


def moving_average(values: List[float], window: int) -> List[float]:
    if window <= 0:
        raise ValueError("window must be > 0")
    if not values:
        return []
    result: List[float] = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        sub = values[start : i + 1]
        result.append(sum(sub) / len(sub))
    return result

