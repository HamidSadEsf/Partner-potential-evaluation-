# src/orchestrator/pipeline.py
"""
LangGraph‑based DAG orchestrating the three agents:
    ResearchAgent → (if missing_fraction ≤ 0.30) → ScoringAgent
                ↘ (otherwise) → SynthesisAgent.generate_data_gap_report()
All agents are mocked for now – they return static Pydantic objects.
The DAG respects the 5 s timeout & 2‑retry policy for the ResearchAgent.
"""

import asyncio
import logging
from typing import Any, TypedDict, Optional

from langgraph.graph import StateGraph, START, END

# Import schemas
from ..schemas.partner_raw_data import PartnerRawData
from ..schemas.partner_score import PartnerScore, RiskComponent
from ..schemas.metadata import Metadata

# -------------------------------------------------------
# Mock agents ------------------------------------------------

async def research_agent(state: dict) -> dict:
    """Mock ResearchAgent – respects timeout/retry policy."""
    max_retries = 2
    timeout_sec = 5
    placeholder = None
    for attempt in range(1, max_retries + 1):
        try:
            raw = await asyncio.wait_for(_fetch_mock_raw_data(), timeout=timeout_sec)
            return {"raw_data": raw}
        except asyncio.TimeoutError:
            logging.warning(
                f"Research call timeout (attempt {attempt}/{max_retries})."
            )
            placeholder = PartnerRawData(
                partner_id="unknown",
                name="unknown",
                regulatory_filings=[],
                compliance_certificates=[],
                tech_stack=[],
                notes=None,
                missing_fraction=min(1.0, 0.15 * attempt),
                metadata=Metadata(
                    reasoning_trace=f"Timeout on attempt {attempt}",
                    model_version="gpt-oss-120b",
                    latency_ms=timeout_sec * 1000,
                    estimated_cost_usd=0.0,
                ),
            )
    return {"raw_data": placeholder}


async def _fetch_mock_raw_data() -> PartnerRawData:
    """Pretend to fetch data – instantly returns a valid object."""
    metadata = Metadata(
        reasoning_trace="Fetched all mandatory fields.",
        model_version="gpt-oss-120b",
        latency_ms=123,
        estimated_cost_usd=0.001,
    )
    return PartnerRawData(
        partner_id="partner-001",
        name="Acme Banking Ltd.",
        regulatory_filings=[],
        compliance_certificates=[],
        tech_stack=[],
        notes=None,
        missing_fraction=0.0,
        metadata=metadata,
    )


async def scoring_agent(state: dict) -> dict:
    """Mock deterministic ScoringAgent – produces a PartnerScore based on raw data."""
    raw: PartnerRawData = state["raw_data"]
    overall_score = 85
    components = [
        {"name": "Regulatory Completeness", "score": 90, "explanation": "All required filings present."},
        {"name": "Tech Maturity", "score": 80, "explanation": "Modern stack with documented APIs."},
    ]
    metadata = Metadata(
        reasoning_trace="Applied rule‑engine scoring.",
        model_version="gpt-oss-120b",
        latency_ms=78,
        estimated_cost_usd=0.0005,
    )
    score = PartnerScore(
        partner_id=raw.partner_id,
        overall_score=overall_score,
        components=[RiskComponent(**c) for c in components],
        overall_confidence_score=0.92,
        recommendation="Proceed with onboarding after standard KYC.",
        recommendation_confidence=0.95,
        metadata=metadata,
    )
    return {"partner_score": score}


async def synthesis_agent(state: dict) -> dict:
    """Mock SynthesisAgent – either a full briefing or a data‑gap report."""
    raw: PartnerRawData = state["raw_data"]
    if raw.missing_fraction > 0.30:
        briefing = (
            f"## Data Gap Report\n"
            f"- Missing {raw.missing_fraction:.0%} of mandatory fields.\n"
            f"- Reasoning Trace: {raw.metadata.reasoning_trace}"
        )
    else:
        briefing = (
            f"## Executive Briefing for {raw.name}\n"
            f"- Overall risk score: 85 (confidence 0.92).\n"
            f"- Recommendation: Proceed with onboarding after standard KYC.\n"
            f"- Reasoning Trace: Synthesized using deterministic scores."
        )
    return {"briefing_markdown": briefing}

class State(TypedDict):
    raw_data: Optional[PartnerRawData]
    partner_score: Optional[PartnerScore]
    briefing_markdown: Optional[str]

# -------------------------------------------------------
# DAG definition ------------------------------------------------

def build_pipeline() -> StateGraph:
    """Constructs the LangGraph DAG with conditional routing based on missing_fraction."""
    graph = StateGraph(State)
    graph.add_node("research", research_agent)
    graph.add_node("scoring", scoring_agent)
    graph.add_node("synthesis", synthesis_agent)
    graph.add_edge(START, "research")

    async def route_after_research(state: dict) -> str:
        raw: PartnerRawData = state["raw_data"]
        return "synthesis" if raw.missing_fraction > 0.30 else "scoring"

    graph.add_conditional_edges(
        "research",
        route_after_research,
        {"scoring": "scoring", "synthesis": "synthesis"},
    )
    graph.add_edge("scoring", "synthesis")
    graph.add_edge("synthesis", END)
    return graph.compile()

# -------------------------------------------------------
# Helper for quick manual testing ------------------------------------------------
async def run_demo() -> None:
    graph = build_pipeline()
    async for state in graph.stream({"raw_data": None}):
        if "partner_score" in state:
            print("\n=== Scoring Result ===")
            print(state["partner_score"].json(indent=2))
        if "briefing_markdown" in state:
            print("\n=== Final Briefing ===")
            print(state["briefing_markdown"])

if __name__ == "__main__":
    asyncio.run(run_demo())
