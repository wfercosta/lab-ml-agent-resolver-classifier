from app.application.ports.llm import LLMPort, LLMRequest
from app.agents.state import AgentState


def classifier_judge_node(llm: LLMPort):
    def _run(state: AgentState) -> AgentState:
        data = llm.invoke_structured(
            LLMRequest(
                prompt_id="classifier-judge-agent",
                variables={"input_text": state["input_text"]},
                correlation_id=state.get("correlation_id"),
            )
        )
        state["agent_classifier_judge"] = data.get("output", "unknown")
        return state

    return _run