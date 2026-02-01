from app.application.ports.llm import LLMPort, LLMRequest
from app.agents.state import AgentState


def resolver_node(llm: LLMPort):
    def _run(state: AgentState) -> AgentState:
        data = llm.invoke_structured(
            LLMRequest(
                prompt_id="resolver-agent",
                variables={"input_text": state["input_text"]},
                correlation_id=state.get("correlation_id"),
            )
        )
        state["agent_resolver"] = data.get("output", "unknown")
        return state

    return _run