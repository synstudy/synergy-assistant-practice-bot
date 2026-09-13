from app import storage
from app.dialog import DialogEngine
from app.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
engine = DialogEngine(kb)


def test_greeting_reply_has_quick_replies():
    result = engine.process("test-greeting", "Здравствуйте")
    assert result["intent"] == "greeting"
    assert result["quick_replies"]
    assert result["state"] == "idle"


def test_fallback_for_unknown():
    result = engine.process("test-fallback", "Расскажи анекдот про ежа")
    assert result["intent"] is None
    assert result["reply"]
    assert result["state"] == "idle"


def test_lead_flow_success():
    session_id = "test-lead-success"
    storage.reset_session(session_id)

    step = engine.process(session_id, "Хочу оставить заявку")
    assert step["state"] == "lead.name"

    step = engine.process(session_id, "Иван")
    assert step["state"] == "lead.phone"

    step = engine.process(session_id, "123")
    assert step["state"] == "lead.phone"

    step = engine.process(session_id, "+7 999 123-45-67")
    assert step["state"] == "lead.program"

    step = engine.process(session_id, "Менеджмент")
    assert step["state"] == "idle"
    assert step["intent"] == "lead_saved"

    leads = storage.get_leads()
    assert any(lead["name"] == "Иван" for lead in leads)


def test_lead_flow_cancel():
    session_id = "test-lead-cancel"
    storage.reset_session(session_id)

    engine.process(session_id, "Хочу поступить")
    result = engine.process(session_id, "отмена")
    assert result["state"] == "idle"
    assert result["intent"] == "lead_cancel"


def test_reset_command():
    session_id = "test-reset"
    engine.process(session_id, "Привет")
    result = engine.process(session_id, "/reset")
    assert result["intent"] == "reset"
    assert result["state"] == "idle"
