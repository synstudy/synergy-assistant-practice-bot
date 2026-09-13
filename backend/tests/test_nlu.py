from app.dialog import DialogEngine
from app.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
engine = DialogEngine(kb)

SYSTEM_INTENTS = {
    "Привет": "greeting",
    "Помощь": "help",
    "/reset": "reset",
    "Оставить заявку": "lead_request",
    "Какая погода?": "weather_general",
}


def test_system_intents():
    for phrase, intent_id in SYSTEM_INTENTS.items():
        intent, _ = engine.detect_intent(phrase)
        assert intent is not None, phrase
        assert intent["id"] == intent_id, phrase


def test_organization_phrases_recognized():
    phrases = [
        "Лицензия",
        "Адрес",
        "Филиалы",
        "Какие нейросети вы используете?",
        "Направления подготовки",
        "Сколько студентов",
        "Выручка",
        "Кто ректор?",
        "Сколько стоит обучение",
        "Как поступить?",
        "Контакты",
        "Бюджетные места",
        "Рейтинги",
        "Гарантия трудоустройства",
    ]
    for phrase in phrases:
        intent, _ = engine.detect_intent(phrase)
        assert intent is not None, phrase


def test_role_intents_are_specific():
    cases = {
        "Кто ректор?": "rektor-universiteta",
        "Кто президент?": "prezident-universiteta",
        "Генеральный директор": "generalnyy-direktor-universiteta",
        "Функции ректора": "funktsii-rektora",
    }
    for phrase, intent_id in cases.items():
        intent, _ = engine.detect_intent(phrase)
        assert intent is not None, phrase
        assert intent["id"] == intent_id, phrase


def test_inflected_keywords():
    intent, _ = engine.detect_intent("Какие специальности есть в вузе")
    assert intent is not None


def test_out_of_domain_topics_fall_back():
    for phrase in ["рецепт борща", "куда поехать", "расписание автобусов"]:
        intent, _ = engine.detect_intent(phrase)
        assert intent is None, phrase


def test_unknown_returns_none():
    intent, score = engine.detect_intent("Квантовая запутанность в лагранжевом формализме")
    assert intent is None
    assert score == 0.0
