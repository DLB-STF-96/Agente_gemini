from typing import Dict
from langchain_core.tools import tool
from .common import find_customer


@tool
def calculate_risk_profile(customer_id: str) -> Dict[str, object]:
    """Determine a basic risk profile (credit-oriented) from credit score and behaviors.

    Output levels: "low", "medium", "high" risk
    """
    customer = find_customer(customer_id)
    if not customer:
        raise ValueError(f"Customer not found: {customer_id}")

    credit = int(customer.get("credit_score", 0))
    churn_signals = customer.get("churn_signals", {}) or {}
    complaints = int(churn_signals.get("complaints_last_6m", 0))
    salary_out = bool(churn_signals.get("salary_moved_out", False))

    base = "medium"
    if credit >= 760:
        base = "low"
    elif credit < 640:
        base = "high"

    score_adjust = 0
    if complaints >= 2:
        score_adjust += 1
    if salary_out:
        score_adjust += 1

    # Map adjustments: low->medium if +1, medium->high if +1, high stays high
    if base == "low" and score_adjust >= 1:
        base = "medium"
    elif base == "medium" and score_adjust >= 1:
        base = "high"

    return {
        "risk_profile": base,
        "credit_score": credit,
        "signals": {
            "complaints_last_6m": complaints,
            "salary_moved_out": salary_out,
        },
    }

