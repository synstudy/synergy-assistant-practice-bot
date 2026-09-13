from app.dialog import DialogEngine
from app.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
engine = DialogEngine(kb)


def test_smalltalk_loaded_alongside_organization():
    assert kb.get_intent("about_university") is not None
    assert kb.get_intent("joke") is not None
    assert len(kb.source_paths) >= 2


def test_joke_intent():
    intent, _ = engine.detect_intent("Расскажи анекдот")
    assert intent["id"] == "joke"


def test_travel_intent():
    intent, _ = engine.detect_intent("Куда поехать в отпуск?")
    assert intent["id"] == "travel_advice"


def test_food_intent():
    intent, _ = engine.detect_intent("Что поесть?")
    assert intent["id"] == "food_advice"


def test_bot_identity_intent():
    intent, _ = engine.detect_intent("Ты бот или человек?")
    assert intent["id"] == "bot_identity"


def test_weather_intent():
    intent, _ = engine.detect_intent("Какая сегодня погода?")
    assert intent["id"] == "weather_general"


def test_organization_topic_not_shadowed():
    intent, _ = engine.detect_intent("Расскажите об университете")
    assert intent["id"] == "about_university"


def test_everyday_reply_is_not_organization():
    result = engine.process("smalltalk-reply", "Расскажи шутку")
    assert result["intent"] == "joke"
    assert result["reply"]
