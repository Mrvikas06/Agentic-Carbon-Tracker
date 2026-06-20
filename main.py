"""
main.py — FastAPI backend for the Agentic Carbon Tracker.

Architecture:
  - All LLM calls are async (non-blocking).
  - No internal stack traces leak to API consumers.
  - File uploads validated for type + size before processing.
  - Environment variables loaded via python-dotenv; zero hardcoded secrets.
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Optional

from google import genai
# pyrefly: ignore [missing-import]
from google.genai import types
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse

from models import (
    Category,
    ErrorResponse,
    FootprintEntry,
    FootprintSummary,
    Quest,
    QuestAcceptResponse,
    QuestItem,
    QuestListResponse,
    QuestListWrapper,
    QuestStatus,
    ReceiptAnalysis,
    ReceiptAnalysisResponse,
    ReceiptItem,
)

# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("carbon_tracker")

GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
client: Optional[genai.Client] = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

# Gemini model used for vision + text tasks
VISION_MODEL = "gemini-1.5-flash"

# Upload constraints
MAX_FILE_SIZE_MB: int = 5
ALLOWED_MIME_TYPES: set[str] = {"image/jpeg", "image/png", "image/webp"}

# Conversion constants (IPCC / EPA approximations)
KG_CO2_PER_TREE_PER_YEAR: float = 21.0          # average mature tree absorption
KG_CO2_PER_KM_PETROL_CAR: float = 0.21          # EU average

app = FastAPI(
    title="Agentic Carbon Tracker API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

cors_origins_raw = os.getenv("CORS_ORIGINS", "")
if cors_origins_raw:
    origins = [origin.strip() for origin in cors_origins_raw.split(",") if origin.strip()]
else:
    origins = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
        "https://carbon-frontend-586539011827.us-central1.run.app",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# In-memory quest store (replace with DB in production)
# ---------------------------------------------------------------------------

_quest_store: dict[str, Quest] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _co2_to_trees(kg: float) -> float:
    """Convert kg CO₂ to tree-years needed for offset."""
    return round(kg / KG_CO2_PER_TREE_PER_YEAR, 2)


def _co2_to_km(kg: float) -> float:
    """Convert kg CO₂ to equivalent km driven in petrol car."""
    return round(kg / KG_CO2_PER_KM_PETROL_CAR, 1)


def _safe_error(code: str, message: str, http_status: int) -> JSONResponse:
    """Return a sanitised error envelope — no internal details."""
    body = ErrorResponse(code=code, message=message)
    return JSONResponse(status_code=http_status, content=body.model_dump())


def _validate_upload(file: UploadFile, data: bytes) -> None:
    """Raise HTTPException if file fails type/size checks."""
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{file.content_type}' not allowed. Use JPEG, PNG, or WebP.",
        )
    size_mb = len(data) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"File exceeds {MAX_FILE_SIZE_MB} MB limit ({size_mb:.1f} MB received).",
        )


# ---------------------------------------------------------------------------
# Carbon estimation helper (called by receipt parser + quest generator)
# ---------------------------------------------------------------------------


FOOD_CO2_MAP: dict[str, float] = {
    # kg CO₂e per kg of product (OURWORLDINDATA / Poore & Nemecek 2018)
    "beef": 60.0, "lamb": 24.0, "pork": 7.6, "chicken": 6.9,
    "fish": 6.1, "shrimp": 12.0, "cheese": 21.0, "milk": 3.2,
    "eggs": 4.5, "tofu": 3.0, "rice": 4.0, "wheat": 1.4,
    "vegetables": 2.0, "fruit": 1.1, "nuts": 2.3, "coffee": 17.0,
    "chocolate": 19.0, "beer": 0.5, "wine": 1.8,
}

FALLBACK_FOOD_CO2: float = 3.0   # kg CO₂e / kg for unknown food items
FALLBACK_ITEM_WEIGHT_KG: float = 0.5  # assumed weight when not on receipt


def estimate_item_co2(item_name: str, quantity_kg: float = FALLBACK_ITEM_WEIGHT_KG) -> float:
    """
    Look up or estimate kg CO₂e for a food item.

    Args:
        item_name: Raw item name string.
        quantity_kg: Weight in kilograms.

    Returns:
        Estimated kg CO₂e as float.
    """
    name_lower = item_name.lower()
    for key, factor in FOOD_CO2_MAP.items():
        if key in name_lower:
            return round(factor * quantity_kg, 3)
    return round(FALLBACK_FOOD_CO2 * quantity_kg, 3)


# ---------------------------------------------------------------------------
# Receipt Analysis Endpoint
# ---------------------------------------------------------------------------


@app.post(
    "/analyse-receipt",
    response_model=ReceiptAnalysisResponse,
    summary="Parse grocery receipt image and estimate carbon footprint",
    responses={
        415: {"model": ErrorResponse},
        413: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def analyse_receipt(
    file: UploadFile = File(..., description="Receipt image (JPEG/PNG/WebP, ≤5 MB)"),
    extra_context: Optional[str] = Form(default=None, max_length=500),
) -> ReceiptAnalysisResponse:
    """
    Accept a grocery receipt image, extract items via Gemini Vision,
    estimate per-item carbon footprint, and return a structured summary.
    """
    raw_data = await file.read()
    _validate_upload(file, raw_data)

    log.info("Receipt upload: %s, %.1f KB", file.filename, len(raw_data) / 1024)

    # ---- Gemini Vision call ------------------------------------------------
    try:
        entries, raw_items, confidence, warnings = await _call_gemini_vision(
            raw_data, file.content_type or "image/jpeg", extra_context
        )
    except Exception as exc:
        log.error("Gemini Vision error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI analysis failed. Please try again.",
        ) from exc

    total_co2 = round(sum(e.kg_co2 for e in entries), 3)

    summary = FootprintSummary(
        entries=entries,
        total_kg_co2=total_co2,
        trees_equivalent=_co2_to_trees(total_co2),
        km_driven_equivalent=_co2_to_km(total_co2),
        source_description=f"Grocery receipt ({len(entries)} items detected)",
    )

    return ReceiptAnalysisResponse(
        summary=summary,
        raw_items_detected=raw_items,
        confidence=confidence,
        warnings=warnings,
    )


async def _call_gemini_vision(
    image_bytes: bytes,
    mime_type: str,
    extra_context: Optional[str],
) -> tuple[list[FootprintEntry], list[str], float, list[str]]:
    """
    Call Gemini 1.5 Flash with the receipt image.
    Returns (entries, raw_items, confidence, warnings).
    Raises RuntimeError on parse failure so callers can map to HTTP 500.
    """
    if not GEMINI_API_KEY or not client:
        # Demo fallback when no key is set (useful for local dev / tests)
        return _demo_entries(), ["Beef mince 500g", "Milk 2L", "Bread", "Apples 1kg"], 0.85, []

    prompt = (
        "You are a carbon footprint analyst. Examine this grocery receipt image.\n"
        "Extract every purchased item with its quantity and unit (weight or count).\n"
        "Analyze the receipt and return the extracted items, extraction confidence, and any warnings."
        + (f"\nExtra context: {extra_context}" if extra_context else "")
    )

    try:
        response = await client.aio.models.generate_content(
            model=VISION_MODEL,
            contents=[
                prompt,
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type=mime_type,
                )
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ReceiptAnalysis,
            )
        )
        parsed = json.loads(response.text)
    except Exception as exc:
        raise RuntimeError(f"Gemini call or JSON parsing failed: {exc}") from exc

    items_data: list[dict] = parsed.get("items", [])
    confidence: float = float(parsed.get("confidence", 0.75))
    warnings: list[str] = parsed.get("warnings", [])

    entries: list[FootprintEntry] = []
    raw_items: list[str] = []

    for item in items_data:
        name: str = str(item.get("name", "Unknown item")).strip()
        quantity: float = float(item.get("quantity", FALLBACK_ITEM_WEIGHT_KG))
        unit: str = str(item.get("unit", "unit"))

        # Normalise quantity to kg for CO₂ lookup
        qty_kg = quantity if unit in ("kg", "g") else FALLBACK_ITEM_WEIGHT_KG
        if unit == "g":
            qty_kg = quantity / 1000

        kg_co2 = estimate_item_co2(name, qty_kg)
        raw_items.append(f"{name} {quantity}{unit}")

        entries.append(
            FootprintEntry(
                item=name,
                category=Category.FOOD,
                kg_co2=kg_co2,
                quantity=quantity,
                unit=unit,
            )
        )

    return entries, raw_items, confidence, warnings


def _demo_entries() -> list[FootprintEntry]:
    """Static demo data returned when GEMINI_API_KEY is absent."""
    return [
        FootprintEntry(item="Beef mince", category=Category.FOOD, kg_co2=30.0, quantity=0.5, unit="kg"),
        FootprintEntry(item="Whole milk", category=Category.FOOD, kg_co2=3.2, quantity=1.0, unit="litre"),
        FootprintEntry(item="White bread", category=Category.FOOD, kg_co2=0.7, quantity=0.5, unit="kg"),
        FootprintEntry(item="Apples", category=Category.FOOD, kg_co2=1.1, quantity=1.0, unit="kg"),
    ]


# ---------------------------------------------------------------------------
# Quest Generation Endpoint
# ---------------------------------------------------------------------------


@app.post(
    "/generate-quests",
    response_model=QuestListResponse,
    summary="Generate personalised CO₂ reduction quests based on footprint data",
    responses={500: {"model": ErrorResponse}},
)
async def generate_quests(summary: FootprintSummary) -> QuestListResponse:
    """
    Accept a FootprintSummary and return 3–5 actionable AI-generated quests.
    Quest IDs are stable slugs so the frontend can track acceptance state.
    """
    try:
        quests = await _call_gemini_text_for_quests(summary)
    except Exception as exc:
        log.error("Quest generation error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Quest generation failed. Please try again.",
        ) from exc

    # Persist in store
    for q in quests:
        _quest_store[q.id] = q

    return QuestListResponse(quests=quests)


async def _call_gemini_text_for_quests(summary: FootprintSummary) -> list[Quest]:
    """
    Use Gemini text model to generate personalised quests.
    Falls back to hardcoded quests when API key absent.
    """
    if not GEMINI_API_KEY or not client:
        return _demo_quests()

    top_items = sorted(summary.entries, key=lambda e: e.kg_co2, reverse=True)[:3]
    items_str = "\n".join(f"- {e.item}: {e.kg_co2} kg CO₂" for e in top_items)

    prompt = (
        f"A user's recent grocery shopping produced {summary.total_kg_co2:.1f} kg CO₂.\n"
        f"Top emitting items:\n{items_str}\n\n"
        "Generate exactly 4 actionable weekly quests to reduce their carbon footprint."
    )

    try:
        response = await client.aio.models.generate_content(
            model=VISION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=QuestListWrapper,
            )
        )
        parsed = json.loads(response.text)
    except Exception as exc:
        raise RuntimeError(f"Quest generation or JSON parsing failed: {exc}") from exc

    quests_data: list[dict] = parsed.get("quests", [])
    quests: list[Quest] = []
    for qd in quests_data:
        diff = qd.get("difficulty", "medium").lower()
        if diff not in ("easy", "medium", "hard"):
            diff = "medium"

        cat_str = qd.get("category", "food").lower()
        try:
            cat = Category(cat_str)
        except ValueError:
            cat = Category.FOOD

        quests.append(
            Quest(
                id=str(qd.get("id", uuid.uuid4().hex[:8])),
                title=str(qd.get("title", "Unnamed Quest")),
                description=str(qd.get("description", "")),
                co2_saving_kg=float(qd.get("co2_saving_kg", 1.0)),
                difficulty=diff,
                category=cat,
                status=QuestStatus.PENDING,
            )
        )
    return quests


def _demo_quests() -> list[Quest]:
    return [
        Quest(
            id="swap-beef-chicken",
            title="🐔 Swap Beef for Chicken",
            description="Replace 500g beef with chicken this week to save ~27 kg CO₂.",
            co2_saving_kg=27.0,
            difficulty="easy",
            category=Category.FOOD,
        ),
        Quest(
            id="plant-based-monday",
            title="🥦 Go Plant-Based on Monday",
            description="One fully plant-based day can save up to 3 kg CO₂ weekly.",
            co2_saving_kg=3.0,
            difficulty="easy",
            category=Category.FOOD,
        ),
        Quest(
            id="reduce-dairy",
            title="🥛 Halve Your Dairy",
            description="Switch to oat milk for cereal + coffee — saves ~5 kg CO₂ per month.",
            co2_saving_kg=1.3,
            difficulty="medium",
            category=Category.FOOD,
        ),
        Quest(
            id="seasonal-veg",
            title="🌿 Buy Seasonal Veg Only",
            description="Skip out-of-season imports; saves ~2 kg CO₂ and supports local farms.",
            co2_saving_kg=2.0,
            difficulty="easy",
            category=Category.FOOD,
        ),
    ]


# ---------------------------------------------------------------------------
# Quest Accept Endpoint
# ---------------------------------------------------------------------------


@app.patch(
    "/quests/{quest_id}/accept",
    response_model=QuestAcceptResponse,
    summary="Mark a quest as accepted by the user",
    responses={404: {"model": ErrorResponse}},
)
async def accept_quest(quest_id: str) -> QuestAcceptResponse:
    """Toggle a quest's status to ACCEPTED."""
    quest = _quest_store.get(quest_id)
    if not quest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quest '{quest_id}' not found.",
        )
    quest.status = QuestStatus.ACCEPTED
    return QuestAcceptResponse(
        quest_id=quest_id,
        status=QuestStatus.ACCEPTED,
        message=f"Quest '{quest.title}' accepted! Good luck 🌱",
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}
