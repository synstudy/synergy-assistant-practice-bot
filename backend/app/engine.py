from . import weather
from .dialog import DialogEngine
from .knowledge import KnowledgeBase


def build_engine():
    knowledge_base = KnowledgeBase.load()
    engine = DialogEngine(knowledge_base)
    engine.register_resolver("weather", lambda data: weather.resolve(data.get("city", "")))
    return engine
