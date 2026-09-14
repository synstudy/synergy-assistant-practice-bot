from . import nlp_spacy, weather
from .dialog import DialogEngine
from .knowledge import KnowledgeBase


def _city_extractor(text):
    if not nlp_spacy.enabled():
        return None
    return nlp_spacy.city_from_text(text)


def build_engine():
    knowledge_base = KnowledgeBase.load()
    engine = DialogEngine(knowledge_base)
    engine.register_resolver("weather", lambda data: weather.resolve(data.get("city", "")))
    engine.register_extractor("city", _city_extractor)
    return engine
