import os
import logging
from typing import Annotated, Sequence, TypedDict, Dict, Any, List, Tuple

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, SystemMessage
from langgraph.graph.message import add_messages
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from app_tools import TOOLS  # Importa tus tools desde el paquete tools

# Configuración de logging a consola
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("agent")

# Evitar fallar si no se configura la API key (no recomendado para producción)
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = "AIzaSyDBilAFDali0jOuoNuhVVHbR-bGomjnpyY"

# Inicialización del modelo y enlace de herramientas
base_model = init_chat_model("gemini-2.5-flash", model_provider="google_genai")
model = base_model.bind_tools(TOOLS)


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    meta: Dict[str, Any]


def _get_role(msg: BaseMessage) -> str:
    return getattr(msg, "type", None) or getattr(msg, "role", "unknown")


def _get_text(msg: BaseMessage) -> str:
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return content
    try:
        return " ".join(map(str, content))
    except Exception:
        return str(content)


def _tool_call_names(tool_calls) -> list[str]:
    names = []
    try:
        for tc in tool_calls or []:
            name = None
            if isinstance(tc, dict):
                name = tc.get("name") or tc.get("tool") or tc.get("id")
            else:
                name = getattr(tc, "name", None) or getattr(tc, "tool", None) or getattr(tc, "type", None)
            if name:
                names.append(name)
    except Exception:
        pass
    return names


def model_call(state: AgentState) -> AgentState:
    # Log del último mensaje del usuario si es el más reciente
    if state["messages"]:
        last = state["messages"][-1]
        role = _get_role(last).lower()
        if role in ("human", "user"):
            logger.info("[usuario] %s", _get_text(last))

    # Prompt del sistema
    system_prompt = SystemMessage(
        content=(
            "Eres un asistente de banca abierta (open banking). Utiliza herramientas para calcular CLV, riesgo de churn, engagement, afinidad de productos y perfil de riesgo; "
            "analizar comportamiento financiero, patrones de transacciones, condiciones de mercado y evaluación de riesgos integral. "
            "Cuando sea necesario, pide el customer_id (por ejemplo CUST001, CUST002, CUST003). Responde de forma breve y clara."
        )
    )

    # Llamada al modelo
    response = model.invoke([system_prompt] + list(state["messages"]))

    # Log del mensaje del asistente
    msg_text = _get_text(response).strip()
    if msg_text:
        logger.info("[asistente] %s", msg_text)

    # Si el asistente pide usar herramientas, lo indicamos
    tool_calls = getattr(response, "tool_calls", None)
    if tool_calls:
        names = _tool_call_names(tool_calls)
        if names:
            logger.info("-> El asistente solicita invocar herramientas: %s", ", ".join(names))
        else:
            logger.info("-> El asistente solicita invocar herramientas.")

    # Historiales (full y lite) y logging con WHY
    meta = state.get("meta", {}) if isinstance(state, dict) else {}
    full_path = meta.get("full_history_path")
    lite_path = meta.get("lite_history_path")

    def _append(path: str, text: str) -> None:
        if not path:
            return
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception:
            pass

    # Registrar último mensaje del usuario en historial completo
    if state["messages"]:
        last = state["messages"][-1]
        role = _get_role(last).lower()
        if role in ("human", "user"):
            _append(full_path, f"USER: {_get_text(last)}")

    # WHY de herramientas
    if tool_calls:
        names = _tool_call_names(tool_calls)
        why = f"WHY: Para responder a la solicitud del usuario, se usarán herramientas: {', '.join(names)}."
        _append(full_path, why)

    # Registrar respuesta del asistente
    if msg_text:
        _append(full_path, f"ASSISTANT: {msg_text}")
        # En el historial ligero guardamos ambos lados para restaurar luego
        if state["messages"]:
            last = state["messages"][-1]
            if _get_role(last).lower() in ("human", "user"):
                _append(lite_path, f"user: {_get_text(last)}")
        _append(lite_path, f"assistant: {msg_text}")

    return {"messages": [response], "meta": meta}


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]
    wants_tools = bool(getattr(last_message, "tool_calls", None))
    if wants_tools:
        return "continue"
    logger.info("-> No se requieren herramientas. Fin del flujo.")
    return "end"


# ToolNode base
_tool_node = ToolNode(tools=TOOLS)

def tools_with_logging(state: AgentState) -> AgentState:
    # Inspecciona la intención de herramientas desde el último mensaje del asistente
    last_ai = None
    for m in reversed(state["messages"]):
        if _get_role(m).lower() in ("assistant", "ai"):
            last_ai = m
            break

    if last_ai and getattr(last_ai, "tool_calls", None):
        names = _tool_call_names(last_ai.tool_calls)
        if names:
            logger.info("-> Ejecutando herramientas: %s", ", ".join(names))
        else:
            logger.info("-> Ejecutando herramientas...")

    # Ejecuta las herramientas reales
    out = _tool_node.invoke(state)

    # Log de resultados de herramientas
    tool_msgs = out.get("messages", [])
    meta = state.get("meta", {}) if isinstance(state, dict) else {}
    full_path = meta.get("full_history_path")

    def _append(path: str, text: str) -> None:
        if not path:
            return
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception:
            pass

    for tm in tool_msgs:
        if _get_role(tm).lower() in ("tool",):
            name = getattr(tm, "name", None) or getattr(tm, "tool", None) or "tool"
            logger.info("[tool:%s] %s", name, _get_text(tm))
            _append(full_path, f"TOOL:{name} -> {_get_text(tm)}")

    return {"messages": tool_msgs, "meta": meta}


# Construcción del grafo
graph = StateGraph(AgentState)
graph.add_node("our_agent", model_call)
graph.add_node("tools", tools_with_logging)  # usamos el wrapper con logging
graph.set_entry_point("our_agent")
graph.add_conditional_edges(
    "our_agent",
    should_continue,
    {"continue": "tools", "end": END},
)
graph.add_edge("tools", "our_agent")

app = graph.compile()


if __name__ == "__main__":
    customer_id = input("Ingrese Customer ID (e.g., CUST001): ").strip()
    if not customer_id:
        print("Customer ID requerido. Saliendo.")
        raise SystemExit(1)

    base_dir = os.getcwd()
    lite_history_path = os.path.join(base_dir, f"historial_{customer_id}.txt")
    full_history_path = os.path.join(base_dir, f"historial_completo_{customer_id}.txt")

    # Cargar historial previo (solo textos de usuario y asistente)
    history_pairs: List[Tuple[str, str]] = []
    if os.path.exists(lite_history_path):
        try:
            with open(lite_history_path, "r", encoding="utf-8") as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln:
                        continue
                    if ln.startswith("user:"):
                        history_pairs.append(("user", ln[len("user:"):].strip()))
                    elif ln.startswith("assistant:"):
                        history_pairs.append(("assistant", ln[len("assistant:"):].strip()))
        except Exception:
            pass

    # Construir secuencia inicial
    messages_seq: List[Tuple[str, str]] = list(history_pairs)

    print("Escribe tu consulta (exit/salir para terminar).")
    while True:
        user_q = input("> ").strip()
        if not user_q:
            continue
        if user_q.lower() in ("exit", "salir", "quit"):
            print("Hasta luego.")
            break

        messages_seq.append(("user", user_q))
        state_in: Dict[str, Any] = {
            "messages": list(messages_seq),
            "meta": {
                "customer_id": customer_id,
                "lite_history_path": lite_history_path,
                "full_history_path": full_history_path,
            },
        }

        final_state = app.invoke(state_in)

        assistant_text = None
        msgs = final_state.get("messages", [])
        for m in reversed(msgs):
            role = _get_role(m).lower()
            if role in ("assistant", "ai"):
                assistant_text = _get_text(m)
                break

        if not assistant_text:
            assistant_text = "(Sin respuesta)"
        print(assistant_text)

        # Continuar el contexto en memoria
        messages_seq.append(("assistant", assistant_text))