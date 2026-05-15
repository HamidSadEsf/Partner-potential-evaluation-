"""Shared metadata model used by all agent payloads.
"""
from pydantic import BaseModel, Field


class Metadata(BaseModel):
    reasoning_trace: str = Field(
        ..., description="Detailed chain-of-thought produced by the agent."
    )
    model_version: str = Field(
        ..., description="Identifier of the LLM model (e.g., gpt-oss-120b)."
    )
    latency_ms: int = Field(
        ..., ge=0, description="Round-trip latency for the agent call in milliseconds."
    )
    estimated_cost_usd: float = Field(
        ..., ge=0.0, description="Estimated token-based cost of the call."
    )
