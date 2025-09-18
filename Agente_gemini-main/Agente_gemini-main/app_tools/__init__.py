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

TOOLS = [
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

