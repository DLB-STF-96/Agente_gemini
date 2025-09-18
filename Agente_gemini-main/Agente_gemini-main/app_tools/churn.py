from typing import Dict
from langchain_core.tools import tool
from .common import find_customer


@tool
def calculate_churn_risk(customer_id: str) -> Dict[str, float]:
    """Calculate a simple churn risk score (0-1) from behavioral signals.

    Heurística:
    - Más días desde último login aumenta riesgo.
    - Señales de churn (quejas, salida de salario, tendencia del balance) aumentan riesgo.
    - Baja actividad en la app aumenta riesgo.
    """
    customer = find_customer(customer_id)
    if not customer:
        raise ValueError(f"Customer not found: {customer_id}")

    days_since = int(customer.get("days_since_last_login", 999))
    sessions = int(customer.get("app_sessions_last_90d", 0))
    churn = customer.get("churn_signals", {}) or {}

    score = 0.0

    # Días sin login (0-30 -> 0.0-0.4; 60+ -> 0.8)
    if days_since <= 30:
        score += (days_since / 30.0) * 0.4
    elif days_since <= 60:
        score += 0.4 + ((days_since - 30) / 30.0) * 0.4
    else:
        score += 0.8

    # Pocas sesiones (0 -> 0.2, 100+ -> 0)
    session_penalty = max(0.0, 1.0 - min(sessions, 100) / 100.0) * 0.2
    score += session_penalty

    # Señales explícitas
    complaints = int(churn.get("complaints_last_6m", 0))
    if complaints > 0:
        score += min(0.2, complaints * 0.05)
    if bool(churn.get("salary_moved_out", False)):
        score += 0.2
    trend = str(churn.get("balance_trend", "stable"))
    if trend == "down":
        score += 0.15
    elif trend == "up":
        score -= 0.05

    # Clamp
    score = max(0.0, min(1.0, score))

    return {
        "churn_risk": round(score, 3),
        "drivers": {
            "days_since_last_login": days_since,
            "app_sessions_last_90d": sessions,
            "complaints_last_6m": complaints,
            "salary_moved_out": bool(churn.get("salary_moved_out", False)),
            "balance_trend": trend,
        },
    }

