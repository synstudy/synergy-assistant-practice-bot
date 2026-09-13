from app.dialog import DialogEngine
from app.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
engine = DialogEngine(kb)


def test_sources_loaded_alongside_organization():
    assert len(kb.source_paths) >= 2
    assert kb.get_intent("greeting") is not None
    assert kb.get_intent("weather_general") is not None


def test_everyday_phrases_recognized():
    for phrase in ["Как дела", "Кто ты", "Расскажи шутку", "Который час", "Извините", "Плохое настроение", "Интересный факт"]:
        intent, _ = engine.detect_intent(phrase)
        assert intent is not None, phrase


def test_everyday_reply_via_process():
    result = engine.process("smalltalk-process", "Как дела")
    assert result["intent"]
    assert result["reply"]
    assert result["state"] == "idle"


def test_weather_trigger():
    intent, _ = engine.detect_intent("Какая сегодня погода?")
    assert intent["id"] == "weather_general"


def test_organization_topic_not_shadowed():
    intent, _ = engine.detect_intent("Направления подготовки")
    assert intent["id"] == "napravleniya-podgotovki-po-dannym-rosobrnadzora"
