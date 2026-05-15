"""Raw data extracted by the ResearchAgent."""
from typing import List, Optional

from pydantic import BaseModel, Field

from .metadata import Metadata


class FinancialMetric(BaseModel):
    """A single financial datapoint from a filing."""
    name: str = Field(..., description="Metric name (e.g., Revenue).")
    value: float = Field(..., description="Numeric value.")
    unit: Optional[str] = Field(None, description="Optional unit (USD, %, etc.).")


class PartnerRawData(BaseModel):
    partner_id: str = Field(..., description="Stable identifier (e.g., LEI).")
    name: str = Field(..., description="Legal name of the partner.")
    regulatory_filings: List[FinancialMetric] = Field(
        default_factory=list,
        description="Extracted financial metrics from public filings."
    )
    compliance_certificates: List[str] = Field(
        default_factory=list,
        description="List of compliance attestations (e.g., SOC‑2)."
    )
    tech_stack: List[str] = Field(
        default_factory=list,
        description="Tech components disclosed in public docs."
    )
    notes: Optional[str] = Field(None, description="Free‑form notes or observations.")
    # -------------------------------------------------------
    # Resiliency field – populated by ResearchAgent
    missing_fraction: float = Field(
        0.0,
        ge=0.0,
        le=1.0,
        description=(
            "Fraction of mandatory fields that could not be retrieved "
            "(0 = complete, 1 = completely missing)."
        ),
    )
    # -------------------------------------------------------
    metadata: Metadata = Field(..., description="Agent execution metadata.")
