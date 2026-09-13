from . import countries, recipes, weather
from .dialog import DialogEngine
from .knowledge import KnowledgeBase


def build_engine():
    knowledge_base = KnowledgeBase.load()
    engine = DialogEngine(knowledge_base)
    engine.register_resolver("weather", lambda data: weather.resolve(data.get("city", "")))
    engine.register_resolver("recipe", lambda data: recipes.resolve(data.get("dish", "")))
    engine.register_resolver("country", lambda data: countries.resolve(data.get("country", "")))
    return engine
