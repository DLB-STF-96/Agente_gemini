from typing import Dict
import csv
import os
from statistics import mean
from langchain_core.tools import tool
from .common import find_customer, DATA_DIR


def _read_csv(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@tool
def financial_behaviour_analysis(customer_id: str) -> Dict[str, object]:
    """Analyze saving rate, investment appetite, debt-to-income, and payment reliability."""
    customer = find_customer(customer_id)
    if not customer:
        raise ValueError(f"Customer not found: {customer_id}")

    monthly_income = float(customer.get("monthly_income", 0))
    tx_rows = _read_csv(os.path.join(DATA_DIR, "transactions.csv"))
    pay_rows = _read_csv(os.path.join(DATA_DIR, "payments.csv"))
    debt_rows = _read_csv(os.path.join(DATA_DIR, "debts.csv"))

    # Filter by customer
    tx = [r for r in tx_rows if r.get("customer_id") == customer_id and r.get("status") == "success"]
    pays = [r for r in pay_rows if r.get("customer_id") == customer_id]
    debt = next((r for r in debt_rows if r.get("customer_id") == customer_id), None)

    # Saving rate approximation: transfers to Savings over total inflow/outflow
    savings_tx = [float(r["amount"]) for r in tx if r.get("merchant") == "Savings"]
    total_spend = sum(float(r["amount"]) for r in tx)
    saving_rate = (sum(savings_tx) / total_spend) if total_spend > 0 else 0.0

    # Investment appetite: interactions + spending to Investment merchant
    invest_tx = [float(r["amount"]) for r in tx if r.get("merchant") == "Investment"]
    invest_ratio = (sum(invest_tx) / total_spend) if total_spend > 0 else 0.0

    # Debt-to-income
    monthly_debt_service = float(debt.get("monthly_debt_service", 0)) if debt else 0.0
    dti = (monthly_debt_service / monthly_income) if monthly_income > 0 else 0.0

    # Payment reliability
    on_time_flags = [r.get("on_time", "False").lower() == "true" for r in pays]
    reliability = mean(on_time_flags) if on_time_flags else 0.0

    rating = "balanced"
    if dti >= 0.4 or reliability < 0.5:
        rating = "fragile"
    elif saving_rate >= 0.15 and reliability >= 0.9 and dti < 0.2:
        rating = "strong"

    return {
        "saving_rate": round(saving_rate, 3),
        "investment_appetite": round(invest_ratio, 3),
        "debt_to_income": round(dti, 3),
        "payment_reliability": round(reliability, 3),
        "summary_rating": rating,
    }


@tool
def analyze_digital_engagement(customer_id: str) -> Dict[str, object]:
    """Analyze digital engagement with a composite score using app sessions, pushes and recency."""
    from .engagement import calculate_engagement

    base = calculate_engagement.invoke({"customer_id": customer_id})
    score = base.get("engagement_score", 0)
    level = "medium"
    if score >= 75:
        level = "high"
    elif score <= 35:
        level = "low"
    return {
        "engagement_score": score,
        "engagement_level": level,
        "details": base.get("components", {}),
    }

