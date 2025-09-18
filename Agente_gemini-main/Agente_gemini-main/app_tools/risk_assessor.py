from typing import Dict, List
from statistics import mean
from langchain_core.tools import tool
from .churn import calculate_churn_risk
from .financial_behaviour import financial_behaviour_analysis
from .market_intelligence import analyze_market_condition
from .transactions_tools import detect_transaction_anomalies, payment_behavior


def _score_from_level(level: str) -> float:
    return {"low": 0.2, "medium": 0.5, "high": 0.8}.get(level, 0.5)


@tool
def overall_risk_score_calculator(customer_id: str) -> Dict[str, float]:
    """Aggregate overall risk score from churn, payment, financial behaviour, and anomalies."""
    churn = calculate_churn_risk.invoke({"customer_id": customer_id}).get("churn_risk", 0.5)
    pay = payment_behavior.invoke({"customer_id": customer_id}).get("on_time_rate", 0.5)
    fin = financial_behaviour_analysis.invoke({"customer_id": customer_id})
    dti = fin.get("debt_to_income", 0.3)
    anomalies = detect_transaction_anomalies.invoke({"customer_id": customer_id}).get("anomalies", [])

    # Normalize inputs to risk
    pay_risk = 1.0 - pay
    dti_risk = min(1.0, dti)
    anomaly_risk = min(1.0, len(anomalies) * 0.1)

    score = mean([churn, pay_risk, dti_risk, anomaly_risk])
    return {"overall_risk_score": round(score, 3)}


@tool
def categorize_risk(customer_id: str) -> Dict[str, str]:
    """Categorize risk bucket from overall risk score."""
    score = overall_risk_score_calculator.invoke({"customer_id": customer_id}).get("overall_risk_score", 0.5)
    bucket = "medium"
    if score >= 0.7:
        bucket = "high"
    elif score <= 0.35:
        bucket = "low"
    return {"risk_category": bucket}


@tool
def assess_churn_risk(customer_id: str) -> Dict[str, float]:
    """Expose churn risk via the churn risk tool."""
    return calculate_churn_risk.invoke({"customer_id": customer_id})


@tool
def assess_financial_risk(customer_id: str) -> Dict[str, object]:
    """Assess financial risk from DTI and payment reliability."""
    fin = financial_behaviour_analysis.invoke({"customer_id": customer_id})
    pay = payment_behavior.invoke({"customer_id": customer_id})
    dti = fin.get("debt_to_income", 0.0)
    pay_risk = 1.0 - pay.get("on_time_rate", 0.0)
    level = "medium"
    if dti >= 0.45 or pay_risk >= 0.5:
        level = "high"
    elif dti < 0.25 and pay_risk < 0.2:
        level = "low"
    return {"financial_risk": level, "metrics": {"dti": dti, "pay_risk": pay_risk}}


@tool
def assess_operational_risk(customer_id: str) -> Dict[str, object]:
    """Operational risk proxy using anomalies and market conditions."""
    anomalies = detect_transaction_anomalies.invoke({"customer_id": customer_id}).get("anomalies", [])
    market = analyze_market_condition.invoke({})
    vol = market.get("sectors", {}).get("equities", {}).get("volatility_index", 0.2)
    level = "medium"
    if len(anomalies) >= 3 or vol >= 0.3:
        level = "high"
    elif len(anomalies) == 0 and vol < 0.2:
        level = "low"
    return {"operational_risk": level, "context": {"anomaly_count": len(anomalies), "market_volatility": vol}}


@tool
def business_impact(customer_id: str) -> Dict[str, object]:
    """Estimate business impact tier from overall risk and CLV approximation."""
    from .clv import calculate_clv

    overall = overall_risk_score_calculator.invoke({"customer_id": customer_id}).get("overall_risk_score", 0.5)
    clv = calculate_clv.invoke({"customer_id": customer_id}).get("clv_estimate", 0.0)
    tier = "moderate"
    if clv >= 3000 and overall >= 0.6:
        tier = "high"
    elif clv < 1500 and overall < 0.4:
        tier = "low"
    return {"impact_tier": tier, "clv": clv, "overall_risk": overall}


@tool
def risk_factors(customer_id: str) -> Dict[str, List[str]]:
    """List key risk factors detected."""
    churn = calculate_churn_risk.invoke({"customer_id": customer_id})
    fin = financial_behaviour_analysis.invoke({"customer_id": customer_id})
    pay = payment_behavior.invoke({"customer_id": customer_id})
    anomalies = detect_transaction_anomalies.invoke({"customer_id": customer_id})
    factors: List[str] = []
    if churn.get("churn_risk", 0) >= 0.6:
        factors.append("Elevated churn risk")
    if fin.get("debt_to_income", 0) >= 0.4:
        factors.append("High debt-to-income")
    if pay.get("on_time_rate", 1) < 0.7:
        factors.append("Poor payment reliability")
    if anomalies.get("anomalies"):
        factors.append("Transaction anomalies detected")
    return {"factors": factors}


@tool
def recommend_mitigation(customer_id: str) -> Dict[str, List[str]]:
    """Recommend mitigation actions based on identified risks."""
    fac = risk_factors.invoke({"customer_id": customer_id}).get("factors", [])
    recs: List[str] = []
    for f in fac:
        if "churn" in f.lower():
            recs.append("Proactive outreach with tailored offers")
        if "debt-to-income" in f.lower():
            recs.append("Restructure debt, offer lower-rate consolidation")
        if "payment" in f.lower():
            recs.append("Set up autopay reminders and grace options")
        if "anomalies" in f.lower():
            recs.append("Enhanced monitoring and KYC review")
    if not recs:
        recs.append("Maintain current strategy; periodic review")
    return {"mitigations": list(dict.fromkeys(recs))[:6]}


@tool
def define_monitoring(customer_id: str) -> Dict[str, str]:
    """Define monitoring frequency based on risk category."""
    cat = categorize_risk.invoke({"customer_id": customer_id}).get("risk_category", "medium")
    freq = "monthly"
    if cat == "high":
        freq = "weekly"
    elif cat == "low":
        freq = "quarterly"
    return {"monitoring_frequency": freq}

