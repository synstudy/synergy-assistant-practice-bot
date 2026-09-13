from app import storage
from app.engine import build_engine

engine = build_engine()


def test_country_flow_known_country():
    session_id = "country-known"
    storage.reset_session(session_id)

    step = engine.process(session_id, "Расскажи о стране")
    assert step["state"] == "flow.country.country"

    result = engine.process(session_id, "Турция")
    assert result["state"] == "idle"
    assert "Стамбул" in result["reply"]


def test_country_flow_unknown_country():
    session_id = "country-unknown"
    storage.reset_session(session_id)

    engine.process(session_id, "Факты о стране")
    result = engine.process(session_id, "Атлантида")
    assert result["state"] == "idle"
    assert "атлантид" in result["reply"].lower()
