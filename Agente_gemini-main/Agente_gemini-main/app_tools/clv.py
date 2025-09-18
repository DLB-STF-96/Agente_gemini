from typing import Dict
from langchain_core.tools import tool
from .common import find_customer


@tool
def calculate_clv(customer_id: str, monthly_retention_rate: float = 0.92, monthly_margin_rate: float = 0.25, discount_rate_monthly: float = 0.01) -> Dict[str, float]:
    """Estimate Customer Lifetime Value for a banking client.

    Parameters
    - customer_id: ID del cliente.
    - monthly_retention_rate: Probabilidad de retener al cliente por mes (0-1).
    - monthly_margin_rate: Margen sobre gasto transaccional atribuido (0-1).
    - discount_rate_monthly: Tasa de descuento mensual (0-1).

    Método
    - Usa el gasto promedio mensual de los últimos 12 meses.
    - CLV aproximado = (ARPU_margin * retention) / (discount - (1 - retention))
      equivalente a serie geométrica de margen descontado.
    """
    customer = find_customer(customer_id)
    if not customer:
        raise ValueError(f"Customer not found: {customer_id}")

    tx = customer.get("transactions_last_12m", [])
    if not tx:
        raise ValueError("transactions_last_12m missing")

    avg_monthly_spend = float(sum(tx)) / max(1, len(tx))
    arpu_margin = avg_monthly_spend * float(monthly_margin_rate)
    r = float(monthly_retention_rate)
    d = float(discount_rate_monthly)

    # Seguridad para evitar división por cero en fórmulas extremas
    denom = d + (1.0 - r)
    if denom <= 0:
        denom = 0.0001

    clv = arpu_margin * r / denom
    return {
        "avg_monthly_spend": round(avg_monthly_spend, 2),
        "arpu_margin": round(arpu_margin, 2),
        "monthly_retention_rate": r,
        "discount_rate_monthly": d,
        "clv_estimate": round(clv, 2),
    }

