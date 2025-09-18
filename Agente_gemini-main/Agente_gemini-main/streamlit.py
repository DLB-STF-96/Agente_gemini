import os
import sys
from typing import Any, Dict, List, Tuple

import streamlit as st


# Ensure local package imports work when running from repo root
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)


st.set_page_config(page_title="Agente Open Banking", page_icon="💳", layout="wide")


def init_environment(api_key: str) -> None:
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key.strip()


@st.cache_resource(show_spinner=False)
def load_backend():
    # Import after env var is set to ensure the model initializes with user key
    from app_tools import get_tools_for_role, tool_names, TOOLS_BASIC, TOOLS_CLIENT_PREMIUM, TOOLS_EXECUTIVE
    from app_tools.common import find_customer
    import main as agent_main
    return {
        "get_tools_for_role": get_tools_for_role,
        "tool_names": tool_names,
        "TOOLS_BASIC": TOOLS_BASIC,
        "TOOLS_CLIENT_PREMIUM": TOOLS_CLIENT_PREMIUM,
        "TOOLS_EXECUTIVE": TOOLS_EXECUTIVE,
        "find_customer": find_customer,
        "agent_app": agent_main.app,
    }


def compute_history_paths(role: str, customer_id: str) -> Tuple[str, str]:
    base_dir = os.getcwd()
    if role == "ejecutivo":
        lite_history_path = os.path.join(base_dir, f"historial_ex_{customer_id}.txt")
        full_history_path = os.path.join(base_dir, f"historial_ex_{customer_id}_completo.txt")
    else:
        lite_history_path = os.path.join(base_dir, f"historial_{customer_id}.txt")
        full_history_path = os.path.join(base_dir, f"historial_{customer_id}_completo.txt")
    return lite_history_path, full_history_path


def load_lite_history(path: str) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln:
                        continue
                    if ln.startswith("user:"):
                        pairs.append(("user", ln[len("user:"):].strip()))
                    elif ln.startswith("assistant:"):
                        pairs.append(("assistant", ln[len("assistant:"):].strip()))
        except Exception:
            pass
    return pairs


def summarize_history(pairs: List[Tuple[str, str]]) -> str:
    if not pairs:
        return ""
    # Build a concise, professional summary using the same LLM
    try:
        from langchain.chat_models import init_chat_model

        base = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
        # Limit to last 20 lines to keep prompt compact
        limited = pairs[-20:]
        convo = "\n".join([f"{r.upper()}: {t}" for r, t in limited])
        prompt = (
            "Eres un asesor financiero profesional. Resume de forma breve y clara (2-4 oraciones) la conversación anterior entre el cliente y el agente. "
            "Enfatiza: qué solicitó el usuario, qué análisis/herramientas utilizó el agente y qué conclusiones o recomendaciones se entregaron. "
            "Evita detalles menores y redacta en español natural y profesional. Si procede, sugiere un siguiente paso en una sola oración.\n\n"
            f"Conversación (últimos turnos):\n{convo}\n\nResumen:"
        )
        msg = base.invoke(prompt)
        content = getattr(msg, "content", msg)
        summary = content if isinstance(content, str) else str(content)
        return summary.strip()
    except Exception:
        # Fallback simple summary if LLM fails
        last_user = next((t for r, t in reversed(pairs) if r == "user"), "")
        last_assistant = next((t for r, t in reversed(pairs) if r == "assistant"), "")
        turns = max(1, len([1 for r, _ in pairs if r == "user"]))
        return (
            f"En nuestra plática anterior tuvimos {turns} consulta(s). "
            f"Me pediste: '{last_user}' y te compartí: '{last_assistant}'."
        )


def render_sidebar(backend: Dict[str, Any], role: str, client_tier: str | None):
    st.sidebar.header("Herramientas disponibles")

    # Mostrar herramientas por grupos
    basic = backend["TOOLS_BASIC"]
    premium = backend["TOOLS_CLIENT_PREMIUM"]
    executive = backend["TOOLS_EXECUTIVE"]

    allowed = backend["get_tools_for_role"](role, client_tier)
    allowed_names = set(backend["tool_names"](allowed))

    def list_tools(title: str, tools: List[Any]):
        with st.sidebar.expander(title, expanded=False):
            for t in tools:
                name = getattr(t, "name", getattr(t, "__name__", str(t)))
                enabled = name in allowed_names
                st.write(("✅ " if enabled else "⛔ ") + name)

    list_tools("Básicas", basic)
    if role == "cliente":
        list_tools("Premium (cliente)", premium)
    if role == "ejecutivo":
        list_tools("Ejecutivo", executive)


def main_ui():
    st.title("Agente Open Banking")

    with st.sidebar:
        st.subheader("Configuración")
        api_key = st.text_input("Google API Key", type="password")
        role = st.selectbox("Rol", options=["cliente", "ejecutivo"], index=0)
        customer_id = st.text_input("Customer ID", value="CUST001")
        ready = st.button("Conectar", type="primary")

    if ready and not api_key:
        st.warning("Por favor ingresa tu API Key.")
        st.stop()

    if ready:
        init_environment(api_key)
        backend = load_backend()

        # Determinar tier del cliente cuando aplique
        client_tier = None
        if role == "cliente":
            cust = backend["find_customer"](customer_id)
            client_tier = (cust or {}).get("tier", "normal")

        st.session_state["backend"] = backend
        st.session_state["role"] = role
        st.session_state["customer_id"] = customer_id
        st.session_state["client_tier"] = client_tier
        lite_path, full_path = compute_history_paths(role, customer_id)
        st.session_state["lite_path"] = lite_path
        st.session_state["full_path"] = full_path
        history_pairs = load_lite_history(lite_path)
        st.session_state.setdefault("messages", [])
        if history_pairs:
            # Show a succinct assistant summary instead of long past history
            summary = summarize_history(history_pairs)
            st.session_state["messages"] = [("assistant", summary)]
        else:
            # Seed initial user message with Customer ID to avoid the agent asking for it
            st.session_state["messages"] = [("user", f"Customer ID: {customer_id}")]
        st.session_state["initialized"] = True
        st.rerun()

    if not st.session_state.get("initialized"):
        st.info("Ingresa tu API Key, selecciona rol e ID de cliente y pulsa Conectar.")
        return

    backend = st.session_state["backend"]
    role = st.session_state["role"]
    customer_id = st.session_state["customer_id"]
    client_tier = st.session_state.get("client_tier")
    render_sidebar(backend, role, client_tier)

    # Mostrar info de tier para clientes
    if role == "cliente":
        tier_label = "Premium" if (client_tier or "normal").lower() == "premium" else "Normal"
        st.caption(f"Cliente: {customer_id} • Tier: {tier_label}")
    else:
        st.caption(f"Ejecutivo conectado • Cliente actual: {customer_id}")

    # Layout: chat + WHY panel
    col_chat, col_why = st.columns([3, 1])

    with col_chat:
        st.subheader("Chat")
        chat_area = st.container()
        with chat_area:
            for role_msg, text in st.session_state.get("messages", []):
                with st.chat_message("user" if role_msg == "user" else "assistant"):
                    st.markdown(text)

        user_q = st.chat_input("Escribe tu consulta…")
        if user_q:
            # Prepare state including the new user message
            runtime_messages = list(st.session_state["messages"]) + [("user", user_q)]
            state_in: Dict[str, Any] = {
                "messages": runtime_messages,
                "meta": {
                    "customer_id": customer_id,
                    "lite_history_path": st.session_state["lite_path"],
                    "full_history_path": st.session_state["full_path"],
                    "role": role,
                    "client_tier": client_tier,
                },
            }

            # Show user's message and waiting indicator in the chat area (above input)
            with chat_area:
                with st.chat_message("user"):
                    st.markdown(user_q)
                with st.chat_message("assistant"):
                    with st.spinner("Esperando respuesta del agente…"):
                        final_state = backend["agent_app"].invoke(state_in)

                # Extract assistant final response
                assistant_text = None
                for m in reversed(final_state.get("messages", [])):
                    role_m = getattr(m, "type", None) or getattr(m, "role", "")
                    if str(role_m).lower() in ("assistant", "ai"):
                        content = getattr(m, "content", "")
                        assistant_text = content if isinstance(content, str) else str(content)
                        break
                if not assistant_text:
                    assistant_text = "(Sin respuesta)"
                st.markdown(assistant_text)

            # Persist both sides and WHY, then re-render
            st.session_state["messages"].append(("user", user_q))
            st.session_state["messages"].append(("assistant", assistant_text))
            st.session_state["last_why"] = final_state.get("meta", {}).get("last_why", "")
            st.rerun()

    with col_why:
        st.subheader("Herramientas ejecutadas")
        why_text = st.session_state.get("last_why", "")
        st.text_area("Razonamiento de herramientas", value=why_text, height=200, label_visibility="collapsed")


if __name__ == "__main__":
    main_ui()

