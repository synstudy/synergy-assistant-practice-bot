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


def test_travel_extended_intents():
    assert engine.detect_intent("Когда лучше ехать?")[0]["id"] == "travel_when"
    assert engine.detect_intent("Сколько брать с собой?")[0]["id"] == "travel_budget"
    assert engine.detect_intent("Безопасность в поездке")[0]["id"] == "travel_safety"
    assert engine.detect_intent("Как оформить визу?")[0]["id"] == "visa_process"
    assert engine.detect_intent("Как платить за границей?")[0]["id"] == "money_payment"
    assert engine.detect_intent("Что положить в ручную кладь?")[0]["id"] == "hand_luggage"


def test_food_extended_intents():
    assert engine.detect_intent("Как выбрать рецепт?")[0]["id"] == "recipe_choice"
    assert engine.detect_intent("Советы новичкам")[0]["id"] == "cooking_tips"
    assert engine.detect_intent("Как выбрать заведение?")[0]["id"] == "cafe_choice"
    assert engine.detect_intent("Что заказать в кафе?")[0]["id"] == "cafe_order"


def test_smalltalk_extended_intents():
    assert engine.detect_intent("Извините")[0]["id"] == "apology"
    assert engine.detect_intent("У меня плохое настроение")[0]["id"] == "bad_mood"
    assert engine.detect_intent("Влияет ли погода на настроение?")[0]["id"] == "weather_mood"
    assert engine.detect_intent("Что делать в дождливый день?")[0]["id"] == "rainy_day"
