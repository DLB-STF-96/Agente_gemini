from typing import Dict, List, Tuple
import csv
import os
from statistics import mean
from datetime import datetime
from langchain_core.tools import tool
from .common import DATA_DIR


def _read_csv(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _tx_for_customer(customer_id: str) -> List[dict]:
    rows = _read_csv(os.path.join(DATA_DIR, "transactions.csv"))
    out = [r for r in rows if r.get("customer_id") == customer_id]
    # sort by date
    for r in out:
        r["_dt"] = datetime.strptime(r["date"], "%Y-%m-%d")
        r["amount"] = float(r["amount"])
    out.sort(key=lambda r: r["_dt"])
    return out


@tool
def summarize_transactions(customer_id: str) -> Dict[str, object]:
    """Return summary of transactions: total amount, count, average amount, successful count."""
    tx = _tx_for_customer(customer_id)
    total_amount = sum(r["amount"] for r in tx)
    count = len(tx)
    avg = (total_amount / count) if count > 0 else 0.0
    success_count = sum(1 for r in tx if r.get("status") == "success")
    return {
        "total_amount": round(total_amount, 2),
        "transaction_count": count,
        "average_amount": round(avg, 2),
        "successful_transactions": success_count,
    }


@tool
def trending_forecast(customer_id: str) -> Dict[str, object]:
    """Naive forecast of next 1, 3, 6 months spend using simple moving average of last 3 months."""
    tx = _tx_for_customer(customer_id)
    if not tx:
        return {"forecast": {"1m": 0.0, "3m": 0.0, "6m": 0.0}}

    # Aggregate by month
    monthly: Dict[str, float] = {}
    for r in tx:
        key = r["_dt"].strftime("%Y-%m")
        monthly[key] = monthly.get(key, 0.0) + r["amount"]

    months_sorted = sorted(monthly.keys())
    last_vals = [monthly[m] for m in months_sorted[-3:]]
    if not last_vals:
        last_vals = [0.0]
    baseline = mean(last_vals)
    return {
        "method": "moving_average_3m",
        "history_tail": last_vals,
        "forecast": {
            "1m": round(baseline, 2),
            "3m": round(baseline * 3, 2),
            "6m": round(baseline * 6, 2),
        },
    }


@tool
def payment_behavior(customer_id: str) -> Dict[str, object]:
    """Assess payment timeliness and consistency from payments.csv."""
    rows = _read_csv(os.path.join(DATA_DIR, "payments.csv"))
    pays = [r for r in rows if r.get("customer_id") == customer_id]
    if not pays:
        return {"on_time_rate": 0.0, "summary": "no payment records"}
    on_time_rate = mean([(r.get("on_time", "False").lower() == "true") for r in pays])
    avg_amount = mean([float(r["amount"]) for r in pays])
    summary = "reliable payer" if on_time_rate >= 0.85 else ("inconsistent" if on_time_rate >= 0.6 else "often late")
    return {
        "on_time_rate": round(on_time_rate, 3),
        "average_payment_amount": round(avg_amount, 2),
        "summary": summary,
        "records": len(pays),
    }


@tool
def detect_transaction_anomalies(customer_id: str, z_threshold: float = 2.0) -> Dict[str, object]:
    """Detect simple anomalies using z-score on amounts per customer."""
    tx = _tx_for_customer(customer_id)
    amounts = [r["amount"] for r in tx if r.get("status") == "success"]
    if len(amounts) < 3:
        return {"anomalies": []}
    mu = mean(amounts)
    var = mean([(a - mu) ** 2 for a in amounts])
    std = var ** 0.5 if var > 0 else 0.0
    anomalies: List[Tuple[str, float, float]] = []
    for r in tx:
        if r.get("status") != "success":
            continue
        if std == 0:
            z = 0.0
        else:
            z = (r["amount"] - mu) / std
        if abs(z) >= z_threshold:
            anomalies.append((r["date"], r["amount"], round(z, 2)))
    return {
        "mean": round(mu, 2),
        "std": round(std, 2),
        "threshold": z_threshold,
        "anomalies": anomalies,
    }

