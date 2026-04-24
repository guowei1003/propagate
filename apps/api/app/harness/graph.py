from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph


class HarnessGraphState(TypedDict, total=False):
    task_id: str
    run_id: str
    mission: dict
    selected_agents: list[dict]
    plan: dict
    current_step_index: int
    pending_approval: bool
    status: str


def build_task_graph():
    graph = StateGraph(HarnessGraphState)

    graph.add_node("intake_node", lambda state: {"status": state.get("status", "intake_complete")})
    graph.add_node("agent_selection_node", lambda state: state)
    graph.add_node("plan_compile_node", lambda state: state)
    graph.add_node("approval_gate_node", lambda state: state)
    graph.add_node("step_dispatch_node", lambda state: state)
    graph.add_node("step_execute_node", lambda state: state)
    graph.add_node("step_verify_node", lambda state: state)
    graph.add_node("supervisor_review_node", lambda state: state)
    graph.add_node("replan_node", lambda state: state)
    graph.add_node("finalize_node", lambda state: {"status": "completed"})

    graph.add_edge(START, "intake_node")
    graph.add_edge("intake_node", "agent_selection_node")
    graph.add_edge("agent_selection_node", "plan_compile_node")
    graph.add_edge("plan_compile_node", "approval_gate_node")
    graph.add_edge("approval_gate_node", "step_dispatch_node")
    graph.add_edge("step_dispatch_node", "step_execute_node")
    graph.add_edge("step_execute_node", "step_verify_node")
    graph.add_edge("step_verify_node", "supervisor_review_node")
    graph.add_edge("replan_node", "approval_gate_node")

    def route_after_supervisor(state: HarnessGraphState) -> str:
        if state.get("status") == "needs_replan":
            return "replan_node"
        if state.get("status") in {"completed", "failed", "canceled"}:
            return "finalize_node"
        return "step_dispatch_node"

    graph.add_conditional_edges(
        "supervisor_review_node",
        route_after_supervisor,
        {
            "replan_node": "replan_node",
            "finalize_node": "finalize_node",
            "step_dispatch_node": "step_dispatch_node",
        },
    )
    graph.add_edge("finalize_node", END)
    return graph.compile()
