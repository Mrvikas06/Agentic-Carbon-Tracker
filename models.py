"""
models.py — Pydantic schemas for all API request/response contracts.
All fields typed strictly; no raw dicts cross API boundaries.
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Category(str, Enum):
    """Top-level emission categories."""
    FOOD = "food"
    TRANSPORT = "transport"
    ENERGY = "energy"
    SHOPPING = "shopping"
    OTHER = "other"


class QuestStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    COMPLETED = "completed"


# ---------------------------------------------------------------------------
# Core domain models
# ---------------------------------------------------------------------------


class FootprintEntry(BaseModel):
    """Single line-item emission record."""
    item: str = Field(..., description="Human-readable item name")
    category: Category
    kg_co2: float = Field(..., ge=0.0, description="Estimated kg CO₂e")
    quantity: float = Field(default=1.0, ge=0.0)
    unit: str = Field(default="unit", description="e.g. kg, litre, km")

    @field_validator("item")
    @classmethod
    def item_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("item must not be blank")
        return v.strip()


class FootprintSummary(BaseModel):
    """Aggregated emission summary returned to the frontend."""
    entries: list[FootprintEntry]
    total_kg_co2: float = Field(..., ge=0.0)
    trees_equivalent: float = Field(
        ..., ge=0.0,
        description="Trees needed for 1 year to offset this amount"
    )
    km_driven_equivalent: float = Field(
        ..., ge=0.0,
        description="Equivalent km in an average petrol car"
    )
    source_description: str = Field(
        ..., description="What was analysed (e.g. 'grocery receipt')"
    )


# ---------------------------------------------------------------------------
# Receipt / upload analysis
# ---------------------------------------------------------------------------


class ReceiptAnalysisRequest(BaseModel):
    """Payload sent from Streamlit to /analyse-receipt (multipart handled separately)."""
    extra_context: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional user note, e.g. 'family of 4'"
    )


class ReceiptItem(BaseModel):
    name: str
    quantity: float
    unit: str


class ReceiptAnalysis(BaseModel):
    items: list[ReceiptItem]
    confidence: float
    warnings: list[str]


class ReceiptAnalysisResponse(BaseModel):
    """Full analysis result returned after receipt parsing."""
    summary: FootprintSummary
    raw_items_detected: list[str] = Field(
        ..., description="Verbatim item list extracted by the vision model"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Model's self-reported extraction confidence"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal issues, e.g. unrecognised items"
    )


# ---------------------------------------------------------------------------
# Quests
# ---------------------------------------------------------------------------


class Quest(BaseModel):
    """AI-generated micro-goal."""
    id: str = Field(..., description="Stable slug, e.g. 'swap-beef-chicken'")
    title: str
    description: str
    co2_saving_kg: float = Field(..., ge=0.0)
    difficulty: str = Field(..., pattern=r"^(easy|medium|hard)$")
    status: QuestStatus = QuestStatus.PENDING
    category: Category


class QuestItem(BaseModel):
    id: str
    title: str
    description: str
    co2_saving_kg: float
    difficulty: str
    category: str


class QuestListWrapper(BaseModel):
    quests: list[QuestItem]


class QuestListResponse(BaseModel):
    quests: list[Quest]


class QuestAcceptRequest(BaseModel):
    quest_id: str = Field(..., min_length=1)


class QuestAcceptResponse(BaseModel):
    quest_id: str
    status: QuestStatus
    message: str


# ---------------------------------------------------------------------------
# Error envelope
# ---------------------------------------------------------------------------


class ErrorResponse(BaseModel):
    """Standardised error body — never exposes internal tracebacks."""
    code: str
    message: str
    detail: Optional[str] = None  # safe human hint only, no stack trace
