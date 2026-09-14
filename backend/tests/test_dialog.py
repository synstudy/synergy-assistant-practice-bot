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
    result = engine.process("test-fallback", "Квантовая запутанность в лагранжевом формализме")
    assert result["intent"] is None
    assert result["reply"]
    assert result["state"] == "idle"


def test_lead_flow_success():
    session_id = "test-lead-success"
    storage.reset_session(session_id)

    step = engine.process(session_id, "Хочу оставить заявку")
    assert step["state"] == "flow.lead.name"

    step = engine.process(session_id, "Иван")
    assert step["state"] == "flow.lead.phone"

    step = engine.process(session_id, "123")
    assert step["state"] == "flow.lead.phone"

    step = engine.process(session_id, "+7 999 123-45-67")
    assert step["state"] == "flow.lead.program"

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


def test_lead_flow_escapes_on_question():
    session_id = "test-lead-escape"
    storage.reset_session(session_id)

    step = engine.process(session_id, "Хочу оставить заявку")
    assert step["state"] == "flow.lead.name"

    result = engine.process(session_id, "Кто ректор?")
    assert result["state"] == "idle"
    assert result["intent"] == "rektor-universiteta"


def test_spacy_matching_disabled_by_default(monkeypatch):
    monkeypatch.delenv("SPACY_ENABLED", raising=False)
    monkeypatch.delenv("SPACY_MATCHING", raising=False)
    local = DialogEngine(KnowledgeBase.load())
    assert local.spacy_matching is False


def test_spacy_matching_uses_content_lemmas(monkeypatch):
    from app import nlp_spacy

    monkeypatch.setenv("SPACY_ENABLED", "true")
    monkeypatch.delenv("SPACY_MATCHING", raising=False)
    monkeypatch.setattr(nlp_spacy, "get_nlp", lambda: (lambda text: []))
    monkeypatch.setattr(nlp_spacy, "content_lemmas", lambda text: {"погода"})
    local = DialogEngine(KnowledgeBase.load())
    assert local.spacy_matching is True

