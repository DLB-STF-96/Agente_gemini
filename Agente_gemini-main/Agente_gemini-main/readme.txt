Agente Open Banking - Visión General para CTO

1) Descripción
 - Agente de banca abierta con herramientas analíticas y LLM para soporte a clientes (normal/premium) y ejecutivos.
 - Orquestado con LangGraph (langgraph) y herramientas (langchain_core.tools).
 - El modelo LLM es Google Gemini (gemini-2.5-flash) a través de langchain chat_models.

2) Estructura de carpetas
 - app_tools/: paquete de herramientas
   - __init__.py: registro de herramientas básicas y LLM, y funciones de gating por rol/tier
   - llm_tools.py: herramientas LLM premium (cliente) y ejecutivo
   - common.py: utilidades, carga de datos
   - *.py: herramientas básicas (CLV, churn, engagement, afinidad, perfil y evaluación de riesgo, transacciones, inteligencia de mercado)
   - data/: datasets (clientes, transacciones, pagos, deudas, sentimiento, competencia, mercado)
 - main.py: agente LangGraph con registro de historiales y WHY
 - streamlit.py: frontend de Streamlit
 - readme.txt: este documento

3) Roles y gating de herramientas
 - Cliente normal: acceso a herramientas básicas.
 - Cliente premium: básicas + LLM premium:
   * investment_strategy_planner
   * investment_proposal_advisor
   * smart_alerts_generator
   * advanced_planning_simulations
 - Ejecutivo: básicas + LLM ejecutivo:
   * executive_sales_opportunity_identifier
   * executive_proactive_retention
   * executive_advanced_lead_scoring
   * executive_kyc_overview

4) Herramientas básicas (principales)
 - CLV: calculate_clv
 - Riesgo de churn: calculate_churn_risk
 - Engagement digital: calculate_engagement, analyze_digital_engagement
 - Afinidad de productos: calculate_product_affinity
 - Perfil de riesgo: calculate_risk_profile
 - Transacciones: summarize_transactions, trending_forecast, payment_behavior, detect_transaction_anomalies
 - Mercado: analyze_market_condition, analyze_competition, customer_sentiment_overview, identify_opportunities, identify_threats, generate_market_recommendations
 - Riesgo integral: overall_risk_score_calculator, categorize_risk, assess_churn_risk, assess_financial_risk, assess_operational_risk, business_impact, risk_factors, recommend_mitigation, define_monitoring

5) Datasets
 - customers.json: incluye tier (normal/premium), campos KYC (status, PEP/AML), señales de churn, engagement, interacciones, etc.
 - transactions.csv: historial de transacciones por cliente.
 - payments.csv: pagos y puntualidad.
 - debts.csv: deuda total y servicio mensual.
 - sentiment.csv: eventos de sentimiento y texto libre.
 - competition.csv: productos de competidores y ofertas.
 - market.json: macro y sectores ampliados.

6) Agente y logging
 - El agente ajusta dinámicamente las herramientas permitidas según meta.role y meta.client_tier usando get_tools_for_role.
 - WHY: main guarda una explicación breve cada vez que el modelo decide usar herramientas (meta["last_why"]).
 - Historiales por rol:
   * Cliente: historial_<id>.txt (ligero), historial_<id>_completo.txt (full con USER/ASSISTANT/TOOL/WHY)
   * Ejecutivo: historial_ex_<id>.txt, historial_ex_<id>_completo.txt

7) Streamlit UI
 - Inputs: API Key de Google, rol (cliente/ejecutivo), Customer ID.
 - Auto-carga de datos del repo; no requiere uploads.
 - Sidebar: lista de herramientas habilitadas por rol/tier y catálogo completo por grupo.
 - Chat: conversación con el agente persistiendo el historial (ligero y completo).
 - Panel Why: muestra la última justificación (WHY) de uso de herramientas.

8) Ejecución
 - CLI (opcional): python main.py -> seguir prompts.
 - Streamlit: streamlit run streamlit.py
   * Requiere variable GOOGLE_API_KEY; la UI la setea en runtime.

9) Seguridad y notas
 - API Key: nunca persistida en disco por el agente; solo en entorno de ejecución.
 - El gating por rol/tier es a nivel de binding de herramientas por invocación.
 - Este proyecto no ejecuta transacciones reales ni accede a datos sensibles fuera de los datasets incluidos.

10) Preguntas sugeridas
 - Cliente (normal):
   * "Dame un resumen de mis transacciones recientes para CUST001."
   * "¿Cuál es mi riesgo de churn para CUST001 y por qué?"
   * "Pronostica mi gasto para los próximos 3 meses en CUST001."
 - Cliente (premium):
   * "Planea mi estrategia de inversión a 5 años para CUST003 con enfoque conservador."
   * "Genera propuestas de inversión comparativas para CUST005."
   * "Crea alertas inteligentes para CUST003 basadas en mis patrones."
   * "Si tomo una hipoteca de 2M a 20 años, ¿cómo afecta mi ahorro en CUST003?"
 - Ejecutivo:
   * "Identifica oportunidades de venta en mi cartera."
   * "¿Qué clientes requieren retención proactiva?"
   * "Haz lead scoring para 'investment' y dame el top 5."
   * "Muéstrame el KYC de CUST002."

