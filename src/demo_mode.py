# src/demo_mode.py
"""
Terminal‑style simulation of the three agents cooperating.
The script runs the LangGraph pipeline defined in `orchestrator/pipeline.py`
with deterministic mock data and pretty‑prints each step, highlighting:

* Agent name
* Latency & cost (from the shared Metadata)
* Confidence scores
* Redaction trigger – if `missing_fraction` > 30 % a warning is shown.
"""

import asyncio
import sys
from datetime import datetime

from .orchestrator.pipeline import build_pipeline

# Simple colour helpers for terminal output
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
CYAN = "\033[36m"


def _log(step: str, message: str, *, level: str = "info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    colour = {"info": CYAN, "warn": YELLOW, "error": RED}.get(level, CYAN)
    sys.stdout.write(f"{colour}{timestamp} [{step}] {message}{RESET}\n")
    sys.stdout.flush()


async def demo():
    _log("SYSTEM", "Launching multi‑agent due‑diligence demo …")
    graph = build_pipeline()
    async for state in graph.astream({"raw_data": None}):
        for node, values in state.items():
            # Research output
            if node == "research":
                raw = values["raw_data"]
                _log(
                    "RESEARCH",
                    f"Fetched data for partner {raw.partner_id} – missing_fraction={raw.missing_fraction:.2%}",
                )
                _log(
                    "RESEARCH",
                    f"Latency: {raw.metadata.latency_ms} ms, Cost: ${raw.metadata.estimated_cost_usd:.4f}",
                )
                if raw.missing_fraction > 0.30:
                    _log(
                        "RESEARCH",
                        "⚠️  Critical data missing – triggering gap‑report path.",
                        level="warn",
                    )
            # Scoring output
            if node == "scoring":
                score = values["partner_score"]
                _log(
                    "SCORING",
                    f"Overall risk {score.overall_score} (confidence {score.overall_confidence_score:.0%})",
                )
                _log(
                    "SCORING",
                    f"Latency: {score.metadata.latency_ms} ms, Cost: ${score.metadata.estimated_cost_usd:.4f}",
                )
            # Synthesis output
            if node == "synthesis":
                briefing = values["briefing_markdown"]
                _log("SYNTHESIS", "Generated briefing:")
                print("\n" + BOLD + GREEN + briefing + RESET + "\n")
                _log(
                    "SYNTHESIS",
                    "Recommendation confidence: 95% (synthetic placeholder)",
                )
                _log("SYSTEM", "Demo completed.")


if __name__ == "__main__":
    asyncio.run(demo())
