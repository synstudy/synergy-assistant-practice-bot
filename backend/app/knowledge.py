import json
import os
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge_base.json"


class KnowledgeBase:
    def __init__(self, data, source_path=None):
        self.meta = data.get("meta", {})
        self.settings = data.get("settings", {})
        self.fallback = data.get("fallback", {"responses": [], "quick_replies": []})
        self.intents = data.get("intents", [])
        self.flows = data.get("flows", {})
        self.source_path = source_path
        self.by_id = {intent["id"]: intent for intent in self.intents}

    def get_intent(self, intent_id):
        return self.by_id.get(intent_id)

    @property
    def default_quick_replies(self):
        return self.settings.get("default_quick_replies", [])

    @property
    def welcome(self):
        return self.meta.get("welcome", "Здравствуйте! Чем могу помочь?")

    @classmethod
    def load(cls, path=None):
        resolved = Path(path or os.environ.get("KNOWLEDGE_BASE_PATH", DEFAULT_PATH))
        with open(resolved, encoding="utf-8") as source:
            return cls(json.load(source), str(resolved))
