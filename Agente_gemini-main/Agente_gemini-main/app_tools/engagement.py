from typing import Dict
from langchain_core.tools import tool
from .common import find_customer


@tool
def calculate_engagement(customer_id: str) -> Dict[str, float]:
    """Compute an engagement score (0-100) based on recent app usage and interactions."""
    customer = find_customer(customer_id)
    if not customer:
        raise ValueError(f"Customer not found: {customer_id}")

    sessions_90d = int(customer.get("app_sessions_last_90d", 0))
    push_opens_90d = int(customer.get("push_opens_last_90d", 0))
    days_since = int(customer.get("days_since_last_login", 999))

    # Score components
    sessions_score = min(1.0, sessions_90d / 100.0) * 50.0
    push_score = min(1.0, push_opens_90d / 50.0) * 30.0
    recency_score = max(0.0, 1.0 - min(days_since, 30) / 30.0) * 20.0

    total = sessions_score + push_score + recency_score
    total = max(0.0, min(100.0, total))

    return {
        "engagement_score": round(total, 1),
        "components": {
            "sessions_score": round(sessions_score, 1),
            "push_score": round(push_score, 1),
            "recency_score": round(recency_score, 1),
        },
    }

