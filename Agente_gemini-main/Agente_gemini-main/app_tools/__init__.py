from .clv import calculate_clv
from .churn import calculate_churn_risk
from .engagement import calculate_engagement
from .affinity import calculate_product_affinity
from .risk_profile import calculate_risk_profile
from .financial_behaviour import financial_behaviour_analysis, analyze_digital_engagement
from .transactions_tools import summarize_transactions, trending_forecast, payment_behavior, detect_transaction_anomalies
from .market_intelligence import (
    analyze_market_condition,
    analyze_competition,
    customer_sentiment_overview,
    identify_opportunities,
    identify_threats,
    generate_market_recommendations,
)
from .risk_assessor import (
    overall_risk_score_calculator,
    categorize_risk,
    assess_churn_risk,
    assess_financial_risk,
    assess_operational_risk,
    business_impact,
    risk_factors,
    recommend_mitigation,
    define_monitoring,
)

# Premium and Executive LLM-based tools (defined in llm_tools.py)
try:
    from .llm_tools import (
        investment_strategy_planner,
        investment_proposal_advisor,
        smart_alerts_generator,
        advanced_planning_simulations,
        executive_sales_opportunity_identifier,
        executive_proactive_retention,
        executive_advanced_lead_scoring,
        executive_kyc_overview,
    )
except Exception:
    # Allow importing base tools even if llm_tools has issues during setup
    investment_strategy_planner = None
    investment_proposal_advisor = None
    smart_alerts_generator = None
    advanced_planning_simulations = None
    executive_sales_opportunity_identifier = None
    executive_proactive_retention = None
    executive_advanced_lead_scoring = None
    executive_kyc_overview = None


# Base tools available to all customers
TOOLS_BASIC = [
    calculate_clv,
    calculate_churn_risk,
    calculate_engagement,
    calculate_product_affinity,
    calculate_risk_profile,
    financial_behaviour_analysis,
    analyze_digital_engagement,
    summarize_transactions,
    trending_forecast,
    payment_behavior,
    detect_transaction_anomalies,
    analyze_market_condition,
    analyze_competition,
    customer_sentiment_overview,
    identify_opportunities,
    identify_threats,
    generate_market_recommendations,
    overall_risk_score_calculator,
    categorize_risk,
    assess_churn_risk,
    assess_financial_risk,
    assess_operational_risk,
    business_impact,
    risk_factors,
    recommend_mitigation,
    define_monitoring,
]


# Premium client-only tools (LLM)
TOOLS_CLIENT_PREMIUM = [
    t for t in [
        investment_strategy_planner,
        investment_proposal_advisor,
        smart_alerts_generator,
        advanced_planning_simulations,
    ] if t is not None
]


# Executive-only tools (LLM)
TOOLS_EXECUTIVE = [
    t for t in [
        executive_sales_opportunity_identifier,
        executive_proactive_retention,
        executive_advanced_lead_scoring,
        executive_kyc_overview,
    ] if t is not None
]


# Full union (legacy export for backwards compatibility)
TOOLS = TOOLS_BASIC + TOOLS_CLIENT_PREMIUM + TOOLS_EXECUTIVE


def tool_names(tools_list):
    try:
        return [getattr(t, "name", getattr(t, "__name__", str(t))) for t in tools_list]
    except Exception:
        return [str(t) for t in tools_list]


def get_tools_for_role(role: str, client_tier: str | None = None):
    role = (role or "").lower()
    tier = (client_tier or "").lower()
    if role in ("ejecutivo", "executive", "ex"):
        return TOOLS_BASIC + TOOLS_EXECUTIVE
    # default: cliente
    if tier in ("premium", "vip"):
        return TOOLS_BASIC + TOOLS_CLIENT_PREMIUM
    return TOOLS_BASIC

