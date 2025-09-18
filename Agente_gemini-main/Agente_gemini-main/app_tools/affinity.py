from typing import Dict, List, Tuple
from langchain_core.tools import tool
from .common import find_customer


PRODUCTS = ["checking", "savings", "credit_card", "personal_loan", "mortgage", "investment", "insurance"]


def _normalize(scores: Dict[str, float]) -> Dict[str, float]:
    total = sum(max(0.0, v) for v in scores.values())
    if total <= 0:
        return {k: 0.0 for k in scores}
    return {k: max(0.0, v) / total for k, v in scores.items()}


@tool
def calculate_product_affinity(customer_id: str, top_k: int = 3) -> Dict[str, object]:
    """Estimate product affinity distribution and return top_k recommendations.

    Combina:
    - Interacciones con productos (señal principal)
    - Productos actuales (ligera penalización para diversificar)
    - Score de crédito para préstamo/mortgage
    """
    customer = find_customer(customer_id)
    if not customer:
        raise ValueError(f"Customer not found: {customer_id}")

    interactions = customer.get("product_interactions", {}) or {}
    owned = set(customer.get("products", []) or [])
    credit = int(customer.get("credit_score", 0))

    base: Dict[str, float] = {p: float(interactions.get(p, 0)) for p in PRODUCTS}

    # Penaliza productos ya poseídos para sugerir cross-sell, pero no los elimina
    for p in owned:
        base[p] *= 0.7

    # Ajustes por credit score: si crédito bajo, reducimos préstamos/mortgage; si alto, potenciamos inversión
    if credit < 680:
        base["personal_loan"] *= 0.6
        base["mortgage"] *= 0.7
    elif credit >= 760:
        base["investment"] *= 1.2

    dist = _normalize(base)
    ranked: List[Tuple[str, float]] = sorted(dist.items(), key=lambda kv: kv[1], reverse=True)
    return {
        "affinity_distribution": {k: round(v, 4) for k, v in dist.items()},
        "top_recommendations": ranked[: max(1, int(top_k))],
    }

