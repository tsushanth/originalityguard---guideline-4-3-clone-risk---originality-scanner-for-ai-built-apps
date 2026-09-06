import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from scan import DEFAULT_THRESHOLD, rank_catalog, verdict  # noqa: E402

# A fixed, deterministic bag-of-words "embedding" over a tiny vocabulary —
# used only so ranking/threshold logic can be tested without downloading
# or running the real sentence-transformers model.
VOCAB = ["habit", "streak", "reminder", "meditation", "sleep", "budget", "chore", "todo"]


def fake_embed(texts):
    return [[text.lower().count(word) for word in VOCAB] for text in texts]


def test_near_duplicate_ranks_first_and_above_threshold():
    app = {
        "name": "HabitFlare",
        "description": "habit streak tracker with reminder",
        "features": ["habit streak", "reminder"],
    }
    catalog = [
        {"id": 1, "name": "StreakForge", "description": "habit streak tracker with reminder and streak badges"},
        {"id": 2, "name": "MindfulMinutes", "description": "meditation and sleep sounds"},
        {"id": 3, "name": "PennyTrail", "description": "budget and expense tracker"},
        {"id": 4, "name": "ChoreChamp", "description": "chore todo list for family"},
    ]

    ranked = rank_catalog(app, catalog, embed_fn=fake_embed)

    assert ranked[0]["name"] == "StreakForge"
    assert ranked[0]["score"] >= DEFAULT_THRESHOLD
    for entry in ranked[1:]:
        assert entry["score"] < DEFAULT_THRESHOLD


def test_verdict_flags_high_clone_risk_above_threshold():
    ranked = [{"id": 1, "name": "StreakForge", "score": 0.95}, {"id": 2, "name": "Other", "score": 0.2}]
    message = verdict(ranked, threshold=DEFAULT_THRESHOLD)
    assert "HIGH CLONE RISK" in message
    assert "StreakForge" in message


def test_verdict_reports_low_risk_below_threshold():
    ranked = [{"id": 1, "name": "Other", "score": 0.1}]
    message = verdict(ranked, threshold=DEFAULT_THRESHOLD)
    assert "LOW risk" in message


def test_verdict_handles_empty_catalog():
    assert "No catalog entries" in verdict([])
