"""
test_app.py — pytest suite for Agentic Carbon Tracker backend.

Coverage:
  - FootprintEntry validation (Pydantic)
  - estimate_item_co2 logic
  - _co2_to_trees / _co2_to_km conversions
  - /analyse-receipt endpoint (mocked Gemini)
  - /generate-quests endpoint (mocked Gemini)
  - /quests/{id}/accept endpoint
  - File upload validation (type + size)
  - Error responses never expose stack traces
"""
from __future__ import annotations

import json
from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

# ---------------------------------------------------------------------------
# Import the app + helpers
# ---------------------------------------------------------------------------

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import (
    app,
    _co2_to_km,
    _co2_to_trees,
    estimate_item_co2,
    _demo_entries,
    _demo_quests,
    _quest_store,
)
from models import (
    Category,
    FootprintEntry,
    FootprintSummary,
    Quest,
    QuestStatus,
)

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def demo_summary() -> FootprintSummary:
    """Reusable footprint summary built from demo entries."""
    entries = _demo_entries()
    total = sum(e.kg_co2 for e in entries)
    return FootprintSummary(
        entries=entries,
        total_kg_co2=total,
        trees_equivalent=_co2_to_trees(total),
        km_driven_equivalent=_co2_to_km(total),
        source_description="Test grocery receipt",
    )


@pytest.fixture(autouse=True)
def clear_quest_store():
    """Reset the in-memory quest store before each test."""
    _quest_store.clear()
    yield
    _quest_store.clear()


# ---------------------------------------------------------------------------
# Unit tests — CO₂ conversion helpers
# ---------------------------------------------------------------------------


class TestCo2Conversions:
    def test_trees_zero(self):
        assert _co2_to_trees(0.0) == 0.0

    def test_trees_one_tree_year(self):
        # 21 kg == 1 tree-year
        assert _co2_to_trees(21.0) == pytest.approx(1.0, rel=1e-3)

    def test_trees_fractional(self):
        result = _co2_to_trees(10.5)
        assert 0 < result < 1

    def test_km_zero(self):
        assert _co2_to_km(0.0) == 0.0

    def test_km_one_kg(self):
        # 1 kg / 0.21 kg/km ≈ 4.8 km
        assert _co2_to_km(1.0) == pytest.approx(4.8, abs=0.1)

    def test_km_large(self):
        assert _co2_to_km(210.0) == pytest.approx(1000.0, rel=1e-3)


# ---------------------------------------------------------------------------
# Unit tests — estimate_item_co2
# ---------------------------------------------------------------------------


class TestEstimateItemCo2:
    def test_known_item_beef(self):
        # 1 kg beef = 60 kg CO₂
        result = estimate_item_co2("beef mince", 1.0)
        assert result == pytest.approx(60.0, rel=1e-3)

    def test_known_item_chicken_partial_weight(self):
        # 0.5 kg chicken = 6.9 * 0.5 = 3.45
        result = estimate_item_co2("chicken breast", 0.5)
        assert result == pytest.approx(3.45, rel=1e-3)

    def test_unknown_item_fallback(self):
        # Unknown items should use FALLBACK_FOOD_CO2 = 3.0 kg/kg
        result = estimate_item_co2("exotic mystery food", 1.0)
        assert result == pytest.approx(3.0, rel=1e-3)

    def test_case_insensitive(self):
        lower = estimate_item_co2("beef", 1.0)
        upper = estimate_item_co2("BEEF", 1.0)
        assert lower == upper

    def test_zero_weight(self):
        result = estimate_item_co2("cheese", 0.0)
        assert result == 0.0

    def test_partial_name_match(self):
        # "beefburger" should still hit "beef" lookup
        result = estimate_item_co2("beefburger", 0.5)
        assert result == pytest.approx(30.0, rel=1e-3)


# ---------------------------------------------------------------------------
# Unit tests — Pydantic models
# ---------------------------------------------------------------------------


class TestFootprintEntryModel:
    def test_valid_entry(self):
        e = FootprintEntry(
            item="Milk",
            category=Category.FOOD,
            kg_co2=3.2,
        )
        assert e.item == "Milk"
        assert e.kg_co2 == 3.2

    def test_blank_item_raises(self):
        with pytest.raises(ValidationError):
            FootprintEntry(item="  ", category=Category.FOOD, kg_co2=1.0)

    def test_negative_co2_raises(self):
        with pytest.raises(ValidationError):
            FootprintEntry(item="Milk", category=Category.FOOD, kg_co2=-1.0)

    def test_item_stripped(self):
        e = FootprintEntry(item="  Apples  ", category=Category.FOOD, kg_co2=1.1)
        assert e.item == "Apples"


# ---------------------------------------------------------------------------
# Integration tests — /analyse-receipt
# ---------------------------------------------------------------------------


DEMO_JPEG_1PX = (
    b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
    b"\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t"
    b"\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a"
    b"\x1f\x1e\x1d\x1a\x1c\x1c $.' \",#\x1c\x1c(7),\x01\x02\x03"
    b"\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4"
    b"\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b"
    b"\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xf5\x0b\xff\xd9"
)


class TestAnalyseReceiptEndpoint:
    """All Gemini calls are mocked — no live API required."""

    def _post_receipt(self, file_bytes=DEMO_JPEG_1PX, content_type="image/jpeg"):
        return client.post(
            "/analyse-receipt",
            files={"file": ("receipt.jpg", BytesIO(file_bytes), content_type)},
            data={"extra_context": "test run"},
        )

    @patch("main.GEMINI_API_KEY", "")  # force demo path
    def test_success_demo_mode(self):
        resp = self._post_receipt()
        assert resp.status_code == 200
        body = resp.json()
        assert "summary" in body
        assert body["summary"]["total_kg_co2"] > 0
        assert len(body["summary"]["entries"]) > 0
        assert 0 <= body["confidence"] <= 1

    @patch("main.GEMINI_API_KEY", "")
    def test_response_contains_trees_equivalent(self):
        resp = self._post_receipt()
        assert resp.status_code == 200
        assert resp.json()["summary"]["trees_equivalent"] > 0

    def test_invalid_file_type_rejected(self):
        resp = client.post(
            "/analyse-receipt",
            files={"file": ("doc.pdf", BytesIO(b"%PDF-1.4"), "application/pdf")},
        )
        assert resp.status_code == 415

    def test_oversized_file_rejected(self):
        big_file = b"x" * (6 * 1024 * 1024)  # 6 MB > 5 MB limit
        resp = self._post_receipt(file_bytes=big_file)
        assert resp.status_code == 413

    @patch("main.GEMINI_API_KEY", "fake-key")
    @patch("main._call_gemini_vision", new_callable=AsyncMock)
    def test_gemini_error_returns_500_no_traceback(self, mock_vision):
        mock_vision.side_effect = RuntimeError("Simulated Gemini timeout")
        resp = self._post_receipt()
        assert resp.status_code == 500
        body = resp.json()
        # Must not expose raw exception text
        assert "RuntimeError" not in body.get("detail", "")
        assert "Traceback" not in str(body)

    @patch("main.GEMINI_API_KEY", "fake-key")
    @patch("main._call_gemini_vision", new_callable=AsyncMock)
    def test_mocked_gemini_response(self, mock_vision):
        mock_entries = [
            FootprintEntry(item="Salmon", category=Category.FOOD, kg_co2=3.05, unit="kg"),
        ]
        mock_vision.return_value = (mock_entries, ["Salmon 0.5kg"], 0.9, [])
        resp = self._post_receipt()
        assert resp.status_code == 200
        body = resp.json()
        assert body["summary"]["entries"][0]["item"] == "Salmon"
        assert body["confidence"] == 0.9


# ---------------------------------------------------------------------------
# Integration tests — /generate-quests
# ---------------------------------------------------------------------------


class TestGenerateQuestsEndpoint:
    @patch("main.GEMINI_API_KEY", "")  # force demo path
    def test_success_demo_mode(self, demo_summary):
        resp = client.post("/generate-quests", json=demo_summary.model_dump())
        assert resp.status_code == 200
        body = resp.json()
        quests = body["quests"]
        assert len(quests) >= 1
        for q in quests:
            assert q["co2_saving_kg"] >= 0
            assert q["difficulty"] in ("easy", "medium", "hard")

    @patch("main.GEMINI_API_KEY", "")
    def test_quests_persisted_in_store(self, demo_summary):
        client.post("/generate-quests", json=demo_summary.model_dump())
        assert len(_quest_store) >= 1

    def test_invalid_summary_schema_rejected(self):
        resp = client.post("/generate-quests", json={"not_valid": True})
        assert resp.status_code == 422  # Pydantic validation error


# ---------------------------------------------------------------------------
# Integration tests — /quests/{id}/accept
# ---------------------------------------------------------------------------


class TestAcceptQuestEndpoint:
    def _seed_quest(self) -> str:
        q = _demo_quests()[0]
        _quest_store[q.id] = q
        return q.id

    def test_accept_existing_quest(self):
        qid = self._seed_quest()
        resp = client.patch(f"/quests/{qid}/accept")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == QuestStatus.ACCEPTED
        assert body["quest_id"] == qid

    def test_accept_unknown_quest_returns_404(self):
        resp = client.patch("/quests/nonexistent-quest/accept")
        assert resp.status_code == 404
        body = resp.json()
        assert "detail" in body

    def test_accept_idempotent(self):
        """Accepting an already-accepted quest stays ACCEPTED."""
        qid = self._seed_quest()
        client.patch(f"/quests/{qid}/accept")
        resp = client.patch(f"/quests/{qid}/accept")
        assert resp.status_code == 200
        assert resp.json()["status"] == QuestStatus.ACCEPTED


# ---------------------------------------------------------------------------
# Integration tests — /health
# ---------------------------------------------------------------------------


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
