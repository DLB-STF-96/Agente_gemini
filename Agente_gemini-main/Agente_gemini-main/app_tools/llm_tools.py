from typing import Dict, List, Any
import os

from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

from .affinity import calculate_product_affinity
from .clv import calculate_clv
from .common import load_customers
from .engagement import calculate_engagement
from .financial_behaviour import financial_behaviour_analysis, analyze_digital_engagement
from .market_intelligence import (
    analyze_market_condition,
    customer_sentiment_overview,
    identify_opportunities,
    identify_threats,
)
from .risk_assessor import (
    overall_risk_score_calculator,
    categorize_risk,
    assess_churn_risk,
    assess_financial_risk,
)
from .transactions_tools import summarize_transactions, trending_forecast, detect_transaction_anomalies, payment_behavior


# Initialize model using same provider/key convention as main
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = os.environ.get("GOOGLE_API_KEY", "")
_llm_base = init_chat_model("gemini-2.5-flash", model_provider="google_genai")


def _synthesize(prompt: str) -> str:
    try:
        msg = _llm_base.invoke(prompt)
        # The model may return a message object; extract content as string
        content = getattr(msg, "content", msg)
        return content if isinstance(content, str) else str(content)
    except Exception as e:
        return f"(No se pudo sintetizar con LLM: {e})"


@tool
def investment_strategy_planner(customer_id: str, goal: str = "crecer patrimonio", horizon_years: int = 5) -> Dict[str, Any]:
    """Planificador de estrategia de inversión para clientes premium.
    Toma señales de comportamiento financiero, riesgo y mercado para proponer una asignación objetivo y pasos accionables.
    """
    fin = financial_behaviour_analysis.invoke({"customer_id": customer_id})
    risk = assess_financial_risk.invoke({"customer_id": customer_id})
    dig = analyze_digital_engagement.invoke({"customer_id": customer_id})
    market = analyze_market_condition.invoke({})
    clv = calculate_clv.invoke({"customer_id": customer_id})
    aff = calculate_product_affinity.invoke({"customer_id": customer_id, "top_k": 5})
    txf = trending_forecast.invoke({"customer_id": customer_id})

    prompt = (
        "Eres un asesor financiero experto. Con la siguiente información del cliente, crea una estrategia de inversión clara,"
        " con asignación sugerida por clase de activo (rango), aportaciones mensuales estimadas, control de riesgo y checklist de pasos.\n\n"
        f"Objetivo: {goal}. Horizonte: {horizon_years} años.\n"
        f"Finanzas: {fin}. Riesgo financiero: {risk}. Engagement digital: {dig}.\n"
        f"Mercado: {market}. CLV: {clv}. Afinidad: {aff}. Pronóstico de gasto: {txf}.\n"
        "Devuelve recomendaciones específicas y prudentes, en español, en formato legible por humanos."
    )
    narrative = _synthesize(prompt)
    return {
        "why": "Integra finanzas personales, perfil de riesgo y condiciones de mercado para proponer asignación y aportaciones.",
        "plan": narrative,
    }


@tool
def investment_proposal_advisor(customer_id: str, contexto: str = "") -> Dict[str, Any]:
    """Asesor de propuestas de inversión: genera propuestas comparativas y justificación para clientes premium."""
    opps = identify_opportunities.invoke({"customer_id": customer_id})
    ths = identify_threats.invoke({"customer_id": customer_id})
    aff = calculate_product_affinity.invoke({"customer_id": customer_id, "top_k": 5})
    sentiment = customer_sentiment_overview.invoke({"customer_id": customer_id})
    prompt = (
        "Como asesor senior, elabora 2-3 propuestas de inversión comparativas (conservadora, balanceada, dinámica) para el cliente,"
        " usando oportunidades y amenazas del mercado, afinidad del cliente y su contexto provisto.\n\n"
        f"Contexto adicional: {contexto}\nOportunidades: {opps}\nAmenazas: {ths}\nAfinidad: {aff}\nSentimiento: {sentiment}\n"
        "Incluye para cada propuesta: objetivo, asignación sugerida, costos/fees, riesgos clave y cuándo revisarla."
    )
    narrative = _synthesize(prompt)
    return {
        "why": "Propuestas respaldadas por oportunidades/amenazas de mercado y afinidad del cliente.",
        "proposals": narrative,
    }


@tool
def smart_alerts_generator(customer_id: str) -> Dict[str, Any]:
    """Alertas inteligentes para clientes premium: genera alertas proactivas basadas en anomalías, pagos y sentimiento."""
    anomalies = detect_transaction_anomalies.invoke({"customer_id": customer_id})
    pay = payment_behavior.invoke({"customer_id": customer_id})
    sentiment = customer_sentiment_overview.invoke({"customer_id": customer_id})
    risk = categorize_risk.invoke({"customer_id": customer_id})
    prompt = (
        "Genera una lista priorizada de alertas y sugerencias accionables (máx 6) para el cliente,"
        " considerando anomalías de transacciones, comportamiento de pagos, sentimiento y bucket de riesgo.\n"
        f"Anomalías: {anomalies}\nPagos: {pay}\nSentimiento: {sentiment}\nRiesgo: {risk}"
    )
    narrative = _synthesize(prompt)
    return {
        "why": "Consolida señales operativas y de experiencia para intervenir proactivamente.",
        "alerts": narrative,
    }


@tool
def advanced_planning_simulations(customer_id: str, monto_mortgage: float = 0.0, plazo_anios: int = 20, tasa_anual_pct: float = 9.5) -> Dict[str, Any]:
    """Planeación y simulaciones avanzadas: estima impacto de una hipoteca en la capacidad de ahorro."
    """
    fin = financial_behaviour_analysis.invoke({"customer_id": customer_id})
    ingreso = fin.get("debt_to_income", 0.0)
    saving_rate = fin.get("saving_rate", 0.0)

    # Mortgage monthly payment approximation (annuity formula)
    try:
        r = (tasa_anual_pct / 100.0) / 12.0
        n = max(1, plazo_anios * 12)
        if monto_mortgage > 0 and r > 0:
            cuota = monto_mortgage * (r * (1 + r) ** n) / (((1 + r) ** n) - 1)
        else:
            cuota = 0.0
    except Exception:
        cuota = 0.0

    prompt = (
        "Evalúa cómo afectaría la hipoteca propuesta a la capacidad de ahorro mensual y al perfil de riesgo del cliente."
        f" Datos base: {fin}. Hipoteca: monto={monto_mortgage}, plazo_anios={plazo_anios}, tasa_anual_pct={tasa_anual_pct}.\n"
        "Explica supuestos, impacto en DTI, ahorro esperado y recomendaciones (p. ej. plazos alternativos)."
    )
    narrative = _synthesize(prompt)
    return {
        "why": "Simula flujo de caja con annuity y métricas de comportamiento financiero.",
        "simulation": {
            "hipoteca_mensual_estimada": round(cuota, 2),
            "saving_rate_base": saving_rate,
            "dti_base": ingreso,
        },
        "analysis": narrative,
    }


# Executive tools

def _all_customers() -> List[Dict[str, Any]]:
    return load_customers()


@tool
def executive_sales_opportunity_identifier() -> Dict[str, Any]:
    """Identificador de oportunidades de venta a nivel cartera. Retorna clientes priorizados y tipo de oferta sugerida."""
    customers = _all_customers()
    ranked: List[Dict[str, Any]] = []
    for c in customers:
        cid = c.get("customer_id")
        opps = identify_opportunities.invoke({"customer_id": cid})
        aff = calculate_product_affinity.invoke({"customer_id": cid, "top_k": 3})
        eng = calculate_engagement.invoke({"customer_id": cid})
        score = eng.get("engagement_score", 0)
        ranked.append({
            "customer_id": cid,
            "name": c.get("name"),
            "engagement": score,
            "suggested": opps.get("opportunities", [])[:2],
            "affinity_top": aff.get("top_recommendations", [])
        })
    # Sort by engagement descending as a simple proxy
    ranked.sort(key=lambda x: x.get("engagement", 0), reverse=True)
    return {"why": "Prioriza por engagement y afinidad." , "opportunities": ranked}


@tool
def executive_proactive_retention(threshold: float = 0.55) -> Dict[str, Any]:
    """Retención proactiva: lista clientes con alto riesgo de churn y acciones sugeridas."""
    customers = _all_customers()
    flagged: List[Dict[str, Any]] = []
    for c in customers:
        cid = c.get("customer_id")
        churn = assess_churn_risk.invoke({"customer_id": cid})
        if churn.get("churn_risk", 0) >= threshold:
            recs = [
                "Ofrecer plan de tarifas simplificado",
                "Contactar con gestor dedicado",
                "Bonificar uso digital durante 90 días",
            ]
            flagged.append({"customer_id": cid, "name": c.get("name"), "churn": churn, "actions": recs})
    return {"why": "Activación basada en riesgo de churn.", "at_risk": flagged}


@tool
def executive_advanced_lead_scoring(producto_objetivo: str = "investment") -> Dict[str, Any]:
    """Lead scoring avanzado: clasifica la cartera por propensión a comprar un producto objetivo."""
    customers = _all_customers()
    scored: List[Dict[str, Any]] = []
    for c in customers:
        cid = c.get("customer_id")
        aff = calculate_product_affinity.invoke({"customer_id": cid, "top_k": 7})
        dist = {k: v for k, v in aff.get("affinity_distribution", {}).items()}
        prop = float(dist.get(producto_objetivo, 0.0))
        eng = calculate_engagement.invoke({"customer_id": cid}).get("engagement_score", 0.0)
        sentiment = customer_sentiment_overview.invoke({"customer_id": cid}).get("avg_score", 0.0)
        # Simple blended score
        score = round(0.6 * prop + 0.3 * (eng / 100.0) + 0.1 * max(0.0, (sentiment + 1) / 2), 4)
        scored.append({"customer_id": cid, "name": c.get("name"), "score": score, "signals": {"propensity": prop, "engagement": eng, "sentiment": sentiment}})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return {"why": "Score mezcla afinidad, engagement y sentimiento.", "lead_scoring": scored}


@tool
def executive_kyc_overview(customer_id: str) -> Dict[str, Any]:
    """KYC del cliente: resume estado de verificación, banderas AML/PEP y datos básicos."""
    for c in _all_customers():
        if c.get("customer_id") == customer_id:
            kyc = c.get("kyc", {})
            profile = {
                "customer_id": c.get("customer_id"),
                "name": c.get("name"),
                "age": c.get("age"),
                "credit_score": c.get("credit_score"),
                "tier": c.get("tier"),
                "kyc": kyc,
                "products": c.get("products", []),
            }
            return {"why": "Consolida campos KYC y perfil básico.", "kyc_profile": profile}
    return {"error": "Customer not found"}

