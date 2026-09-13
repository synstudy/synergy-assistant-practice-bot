import json
import os
from pathlib import Path

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge_base.json"
DEFAULT_SMALLTALK_PATH = Path(__file__).resolve().parent.parent / "data" / "smalltalk.json"


class KnowledgeBase:
    def __init__(self, data, source_paths=None):
        self.meta = data.get("meta", {})
        self.settings = data.get("settings", {})
        self.fallback = data.get("fallback", {"responses": [], "quick_replies": []})
        self.intents = data.get("intents", [])
        self.flows = data.get("flows", {})
        self.source_paths = source_paths or []
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
    def load(cls, paths=None):
        resolved = cls._resolve_paths(paths)
        documents = []
        sources = []
        for path in resolved:
            if path.exists():
                with open(path, encoding="utf-8") as source:
                    documents.append(json.load(source))
                sources.append(str(path))
        if not documents:
            raise FileNotFoundError(f"Не найдено ни одного файла базы знаний: {resolved}")
        return cls(cls._merge(documents), sources)

    @staticmethod
    def _resolve_paths(paths):
        if paths is not None:
            if isinstance(paths, (str, Path)):
                paths = [paths]
            return [Path(path) for path in paths]

        primary = Path(os.environ.get("KNOWLEDGE_BASE_PATH", DEFAULT_PATH))
        result = [primary]
        smalltalk = os.environ.get("SMALLTALK_PATH")
        if smalltalk:
            result.append(Path(smalltalk))
        elif DEFAULT_SMALLTALK_PATH.exists():
            result.append(DEFAULT_SMALLTALK_PATH)
        return result

    @classmethod
    def _merge(cls, documents):
        merged = json.loads(json.dumps(documents[0]))
        intents = list(merged.get("intents", []))
        seen = {intent["id"] for intent in intents}
        flows = dict(merged.get("flows", {}))
        extra_quick_replies = []

        for document in documents[1:]:
            for intent in document.get("intents", []):
                if intent.get("id") not in seen:
                    intents.append(intent)
                    seen.add(intent["id"])
            for key, flow in document.get("flows", {}).items():
                flows.setdefault(key, flow)
            extra_quick_replies.extend(document.get("fallback", {}).get("quick_replies", []))

        merged["intents"] = intents
        merged["flows"] = flows
        if extra_quick_replies:
            fallback = merged.setdefault("fallback", {})
            existing = fallback.setdefault("quick_replies", [])
            for reply in extra_quick_replies:
                if reply not in existing:
                    existing.append(reply)
        return merged
