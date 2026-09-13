from app.dialog import DialogEngine
from app.knowledge import KnowledgeBase

kb = KnowledgeBase.load()
engine = DialogEngine(kb)


def test_greeting():
    intent, score = engine.detect_intent("Привет!")
    assert intent["id"] == "greeting"
    assert score > 0


def test_about_university():
    intent, _ = engine.detect_intent("Расскажите об университете")
    assert intent["id"] == "about_university"


def test_address():
    intent, _ = engine.detect_intent("Какой у вас адрес?")
    assert intent["id"] == "address"


def test_branches():
    intent, _ = engine.detect_intent("Сколько у вас филиалов?")
    assert intent["id"] == "branches"


def test_inflected_keywords():
    intent, _ = engine.detect_intent("Какие специальности есть в вузе")
    assert intent["id"] == "programs"


def test_tuition():
    intent, _ = engine.detect_intent("Сколько стоит обучение?")
    assert intent["id"] == "tuition"


def test_ai():
    intent, _ = engine.detect_intent("Какие нейросети вы используете?")
    assert intent["id"] == "ai"


def test_unknown_returns_none():
    intent, score = engine.detect_intent("Квантовая запутанность в лагранжевом формализме")
    assert intent is None
    assert score == 0.0
