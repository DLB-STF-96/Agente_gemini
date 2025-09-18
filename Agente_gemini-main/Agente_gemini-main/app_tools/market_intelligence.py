from typing import Dict, List
import csv
import json
import os
from statistics import mean
from langchain_core.tools import tool
from .common import DATA_DIR


def _read_csv(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


@tool
def analyze_market_condition() -> Dict[str, object]:
    """Analyze macro and sector conditions from market.json."""
    with open(os.path.join(DATA_DIR, "market.json"), "r", encoding="utf-8") as f:
        market = json.load(f)
    macro = market.get("macro", {})
    sectors = market.get("sectors", {})
    outlook = "neutral"
    if macro.get("gdp_growth_qoq_pct", 0) > 0.5 and macro.get("inflation_yoy_pct", 0) < 4.0:
        outlook = "positive"
    if macro.get("unemployment_pct", 0) > 6.5:
        outlook = "cautious"
    return {"macro": macro, "sectors": sectors, "outlook": outlook}


@tool
def analyze_competition() -> Dict[str, object]:
    """Summarize competitive products and value props."""
    rows = _read_csv(os.path.join(DATA_DIR, "competition.csv"))
    by_product: Dict[str, List[dict]] = {}
    for r in rows:
        by_product.setdefault(r["product"], []).append(r)
    highlights = {}
    for p, items in by_product.items():
        aprs = [float(i["apr_pct"]) for i in items]
        best_fee = min(float(i["annual_fee"]) for i in items)
        highlights[p] = {
            "avg_apr": round(mean(aprs), 2),
            "min_annual_fee": best_fee,
            "offers": [i["signup_bonus"] for i in items],
        }
    return {"competition_summary": highlights}


@tool
def customer_sentiment_overview(customer_id: str) -> Dict[str, object]:
    """Aggregate sentiment events for a customer."""
    rows = _read_csv(os.path.join(DATA_DIR, "sentiment.csv"))
    events = [r for r in rows if r.get("customer_id") == customer_id]
    if not events:
        return {"avg_score": 0.0, "events": []}
    scores = [float(r["score"]) for r in events]
    avg = mean(scores)
    mood = "neutral"
    if avg >= 0.4:
        mood = "positive"
    elif avg <= -0.1:
        mood = "negative"
    return {"avg_score": round(avg, 3), "mood": mood, "events": events[-5:]}


@tool
def identify_opportunities(customer_id: str) -> Dict[str, object]:
    """Heuristic opportunities based on market outlook and customer sentiment."""
    market = analyze_market_condition.invoke({})
    sentiment = customer_sentiment_overview.invoke({"customer_id": customer_id})
    opps: List[str] = []
    if market.get("outlook") == "positive":
        opps.append("Promote investment products with low fees")
    if sentiment.get("mood") in ("positive", "neutral"):
        opps.append("Cross-sell high-value credit card")
    opps.append("Offer savings rate boost for 90 days")
    return {"opportunities": opps}


@tool
def identify_threats(customer_id: str) -> Dict[str, object]:
    """Heuristic threats based on competition and negative sentiment."""
    comp = analyze_competition.invoke({})
    sentiment = customer_sentiment_overview.invoke({"customer_id": customer_id})
    threats: List[str] = []
    cc = comp.get("competition_summary", {}).get("credit_card", {})
    if cc and cc.get("min_annual_fee", 999) == 0:
        threats.append("Competitors with zero-fee credit cards")
    if sentiment.get("mood") == "negative":
        threats.append("Customer dissatisfaction could trigger churn")
    return {"threats": threats}


@tool
def generate_market_recommendations(customer_id: str) -> Dict[str, object]:
    """Recommendations combining opportunities and threats."""
    opps = identify_opportunities.invoke({"customer_id": customer_id})
    ths = identify_threats.invoke({"customer_id": customer_id})
    recs = opps.get("opportunities", []) + [f"Mitigate: {t}" for t in ths.get("threats", [])]
    return {"recommendations": recs[:6]}

