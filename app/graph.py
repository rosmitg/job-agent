# app/graph.py

from typing import Optional
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from app.models import ParsedJD, JobRequirementEvidenceMap
from app.agents.jd_parser import parse_jd
from app.agents.profile_loader import load_profile
from app.agents.evidence_matcher import match_evidence, check_filter_gate
from app.agents.resume_generator import generate_resume
from app.agents.evaluator import evaluate_resume
from app.agents.revision_loop import revise_resume

# ─────────────────────────────────────────
# State — flows through every node
# ─────────────────────────────────────────


class AgentState(BaseModel):
    jd_text: str
    parsed_jd: Optional[ParsedJD] = None
    evidence_map: Optional[JobRequirementEvidenceMap] = None
    filter_passed: bool = False
    filter_reasons: list[str] = []
    resume: str = ""
    evaluation: dict = {}
    revision_count: int = 0
    base_resume: str = ""

    class Config:
        arbitrary_types_allowed = True


# ─────────────────────────────────────────
# Nodes
# ─────────────────────────────────────────


def node_parse_jd(state: AgentState) -> AgentState:
    print("\n📋 Parsing job description...")
    parsed = parse_jd(state.jd_text)
    print(f"   Role: {parsed.job_title} at {parsed.company_name}")
    print(f"   Requirements: {len(parsed.requirements)}")
    return state.model_copy(update={"parsed_jd": parsed})


def node_match_evidence(state: AgentState) -> AgentState:
    print("\n🔍 Matching evidence...")
    profile = load_profile()
    evidence_map = match_evidence(state.parsed_jd, profile)
    print(f"   Coverage: {evidence_map.coverage_score:.0%}")
    print(f"   Must-have coverage: {evidence_map.must_have_coverage:.0%}")
    return state.model_copy(update={"evidence_map": evidence_map})


def node_filter_gate(state: AgentState) -> AgentState:
    print("\n🚦 Checking filter gate...")
    passed, reasons = check_filter_gate(state.evidence_map)
    if passed:
        print("   ✅ Passed — proceeding")
    else:
        print("   ❌ Failed — stopping")
        for r in reasons:
            print(f"      {r}")
    return state.model_copy(update={"filter_passed": passed, "filter_reasons": reasons})


def node_generate(state: AgentState) -> AgentState:
    print("\n✍️  Generating resume...")
    profile = load_profile()
    with open("data/base_resume.md") as f:
        base_resume = f.read()
    resume = generate_resume(state.evidence_map, profile)
    print("   Resume generated")
    return state.model_copy(update={"resume": resume, "base_resume": base_resume})


def node_evaluate(state: AgentState) -> AgentState:
    print("\n📊 Evaluating resume...")
    result = evaluate_resume(state.resume, state.evidence_map, state.base_resume)
    score = result["subjective"]["total"]
    print(f"   Score: {score}/25")
    print(f"   Passed: {result['passed']}")
    if result["failures"]:
        for f in result["failures"]:
            print(f"   ❌ {f}")
    return state.model_copy(update={"evaluation": result})


def node_revise(state: AgentState) -> AgentState:
    print(f"\n🔁 Revising (attempt {state.revision_count + 1}/2)...")
    failures = state.evaluation.get("failures", [])
    recommendation = state.evaluation.get("subjective", {}).get("recommendation", "")

    profile = load_profile()
    revised = revise_resume(
        resume=state.resume,
        failures=failures,
        recommendation=recommendation,
        evidence_map=state.evidence_map,
        profile=profile,
        base_resume=state.base_resume,
    )
    print("   Revision complete")
    return state.model_copy(
        update={"resume": revised, "revision_count": state.revision_count + 1}
    )


def node_human_review(state: AgentState) -> AgentState:
    print("\n" + "=" * 50)
    print("✅ HUMAN REVIEW")
    print("=" * 50)
    score = state.evaluation.get("subjective", {}).get("total", 0)
    print(f"Final score:  {score}/25")
    print(f"Revisions:    {state.revision_count}")
    print(f"Filter gate:  {'PASSED' if state.filter_passed else 'FAILED'}")

    with open("output_resume.md", "w") as f:
        f.write(state.resume)
    print("\nResume saved to output_resume.md")
    print("Review before submitting — check all claims are honest.")
    return state


# ─────────────────────────────────────────
# Conditional edge functions
# Return the name of the next node
# ─────────────────────────────────────────


def route_filter(state: AgentState) -> str:
    """
    After filter_gate:
    PASS → go to generate
    FAIL → END (don't apply)
    """
    if state.filter_passed:
        return "generate"
    return END


def route_evaluation(state: AgentState) -> str:
    """
    After evaluate:
    PASS → human_review
    FAIL + revisions remaining → revise
    FAIL + max revisions hit → human_review anyway
    """
    passed = state.evaluation.get("passed", False)
    if passed:
        return "human_review"
    if state.revision_count >= 2:
        print("   ⚠️  Max revisions reached — sending to human review")
        return "human_review"
    return "revise"


# ─────────────────────────────────────────
# Build the graph
# ─────────────────────────────────────────


def build_graph():
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("parse_jd", node_parse_jd)
    graph.add_node("match_evidence", node_match_evidence)
    graph.add_node("filter_gate", node_filter_gate)
    graph.add_node("generate", node_generate)
    graph.add_node("evaluate", node_evaluate)
    graph.add_node("revise", node_revise)
    graph.add_node("human_review", node_human_review)

    # Entry point
    graph.set_entry_point("parse_jd")

    # Regular edges — always execute
    graph.add_edge("parse_jd", "match_evidence")
    graph.add_edge("match_evidence", "filter_gate")
    graph.add_edge("generate", "evaluate")
    graph.add_edge("revise", "evaluate")
    graph.add_edge("human_review", END)

    # Conditional edges — depends on state
    graph.add_conditional_edges(
        "filter_gate", route_filter, {"generate": "generate", END: END}
    )

    graph.add_conditional_edges(
        "evaluate",
        route_evaluation,
        {"human_review": "human_review", "revise": "revise"},
    )

    return graph.compile()


# ─────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────


def run(jd_text: str):
    print("\n" + "=" * 50)
    print("JOB APPLICATION AGENT")
    print("=" * 50)

    graph = build_graph()
    initial_state = AgentState(jd_text=jd_text)
    result = graph.invoke(initial_state)
    return result


if __name__ == "__main__":
    run("""
    AI Engineer at Westpac Sydney.
    Must have Python and LangChain.
    Must have Australian work rights.
    Preferred: Docker, AWS.
    Full time graduate role.
    Build RAG systems for banking.
    """)
