import random
import re

from . import nlp_spacy, storage
from .nlu import lemmatize

_PHONE_RE = re.compile(r"\D")
_QUESTION_STARTS = {
    "кто", "что", "как", "какой", "какая", "какие", "где",
    "когда", "сколько", "почему", "куда", "чем", "каков",
}
_FLOW_QUICK_REPLIES = ["Отмена"]


class DialogEngine:
    def __init__(self, knowledge_base, resolvers=None):
        self.kb = knowledge_base
        self.threshold = float(self.kb.settings.get("match_threshold", 1.0))
        self.resolvers = dict(resolvers or {})
        self.extractors = {}
        self.spacy_matching = self._init_spacy_matching()
        self._index = self._build_index()

    def _init_spacy_matching(self):
        if not nlp_spacy.matching_enabled():
            return False
        try:
            nlp_spacy.get_nlp()
        except Exception:
            return False
        return True

    def register_resolver(self, name, handler):
        self.resolvers[name] = handler

    def register_extractor(self, name, handler):
        self.extractors[name] = handler

    def _lemmas(self, text):
        if self.spacy_matching:
            return frozenset(nlp_spacy.content_lemmas(text))
        return frozenset(lemmatize(text))

    def _build_index(self):
        index = []
        for intent in self.kb.intents:
            patterns = []
            for keyword in intent.get("keywords", []):
                lemmas = self._lemmas(keyword)
                if lemmas:
                    patterns.append((lemmas, len(lemmas)))
            index.append((intent, patterns))
        return index

    def detect_intent(self, text):
        message_lemmas = set(self._lemmas(text))
        best_intent = None
        best_score = 0.0
        for intent, patterns in self._index:
            score = sum(weight for lemmas, weight in patterns if lemmas <= message_lemmas)
            if score > best_score:
                best_score = score
                best_intent = intent
        if best_intent is not None and best_score >= self.threshold:
            return best_intent, best_score
        return None, 0.0

    def _new_session(self):
        return {"state": "idle", "data": {}}

    def _normalize_session(self, session):
        if not session:
            return self._new_session()
        state = session.get("state", "idle")
        if state.startswith("lead."):
            session["state"] = "flow." + state
            if "lead" in session:
                session.setdefault("data", {}).update(session.pop("lead"))
        session.setdefault("data", {})
        return session

    def _parse_command(self, text):
        stripped = text.strip().lower()
        if not stripped.startswith("/"):
            return None
        return stripped[1:].split("@")[0].split()[0] if stripped[1:] else ""

    def _reply(self, reply, quick_replies, state, intent=None):
        return {
            "reply": reply,
            "quick_replies": quick_replies,
            "state": state,
            "intent": intent,
        }

    def _default_quick_replies(self):
        return list(self.kb.default_quick_replies)

    def welcome(self):
        return self.kb.welcome

    def help_text(self):
        intent = self.kb.get_intent("help")
        if intent and intent.get("responses"):
            return intent["responses"][0]
        return "Задайте вопрос об Университете «Синергия»."

    def _reset_reply(self, session_id, message, intent="reset"):
        storage.save_session(session_id, self._new_session())
        return self._reply(message, self._default_quick_replies(), "idle", intent)

    def _flow_by_trigger(self, intent_id):
        for flow_id, flow in self.kb.flows.items():
            if flow.get("trigger") == intent_id:
                return flow_id, flow
        return None, None

    def process(self, session_id, text):
        session = self._normalize_session(storage.get_session(session_id))

        command = self._parse_command(text)
        if command in ("start", "reset", "restart"):
            return self._reset_reply(session_id, self.welcome())
        if command == "help":
            return self._reply(self.help_text(), self._default_quick_replies(), "idle", "help")

        state = session.get("state", "idle")
        if state.startswith("flow."):
            return self._handle_flow(session_id, session, text)

        intent, _score = self.detect_intent(text)

        if intent is None:
            fallback = self.kb.fallback
            return self._reply(
                random.choice(fallback.get("responses") or ["Не понял вопрос."]),
                list(fallback.get("quick_replies") or self._default_quick_replies()),
                "idle",
            )

        if intent["id"] == "reset":
            return self._reset_reply(session_id, random.choice(intent["responses"]))

        flow_id, flow = self._flow_by_trigger(intent["id"])
        if flow:
            return self._start_flow(session_id, flow_id, flow, intent["id"], text)

        replies = intent.get("responses") or ["Пока не могу ответить на это."]
        quick_replies = intent.get("quick_replies")
        if quick_replies is None:
            quick_replies = self._default_quick_replies()
        return self._reply(random.choice(replies), list(quick_replies), "idle", intent["id"])

    def _start_flow(self, session_id, flow_id, flow, intent_id, text=""):
        session = self._new_session()
        for step in flow["steps"]:
            value = self._extract(step.get("extract"), text) if step.get("extract") else None
            if not value:
                session["state"] = f"flow.{flow_id}.{step['key']}"
                storage.save_session(session_id, session)
                return self._reply(step["prompt"], list(_FLOW_QUICK_REPLIES), session["state"], intent_id)
            session["data"][step["key"]] = value
        return self._complete_flow(session_id, session, flow_id, flow)

    def _extract(self, name, text):
        handler = self.extractors.get(name) if name else None
        if handler is None or not text:
            return None
        try:
            return handler(text)
        except Exception:
            return None

    def _looks_like_question(self, text):
        if "?" in text:
            return True
        lemmas = lemmatize(text)
        return bool(lemmas) and lemmas[0] in _QUESTION_STARTS

    def _maybe_escape_flow(self, session_id, flow, text):
        if not self._looks_like_question(text):
            return None
        intent, _score = self.detect_intent(text)
        if intent is None or intent["id"] == flow.get("trigger"):
            return None
        storage.save_session(session_id, self._new_session())
        result = self.process(session_id, text)
        result["reply"] = "Прервал предыдущий сценарий. " + result["reply"]
        return result

    def _handle_flow(self, session_id, session, text):
        flow_id, step_key = self._parse_flow_state(session["state"])
        flow = self.kb.flows.get(flow_id)
        if flow is None:
            storage.save_session(session_id, self._new_session())
            return self._reply("Не получилось продолжить. Начнём заново.", self._default_quick_replies(), "idle")

        if self._is_cancel(text, flow):
            storage.save_session(session_id, self._new_session())
            return self._reply(
                "Хорошо, отменил. Чем ещё могу помочь?",
                self._default_quick_replies(),
                "idle",
                f"{flow_id}_cancel",
            )

        escape = self._maybe_escape_flow(session_id, flow, text)
        if escape is not None:
            return escape

        step = next((item for item in flow["steps"] if item["key"] == step_key), None)
        if step is None:
            storage.save_session(session_id, self._new_session())
            return self._reply("Что-то пошло не так. Начнём заново.", self._default_quick_replies(), "idle")

        value = text.strip()
        error = self._validate(step, value)
        if error:
            return self._reply(error, list(_FLOW_QUICK_REPLIES), session["state"], flow_id)

        session["data"][step["key"]] = value
        index = flow["steps"].index(step)

        if index + 1 < len(flow["steps"]):
            next_step = flow["steps"][index + 1]
            session["state"] = f"flow.{flow_id}.{next_step['key']}"
            storage.save_session(session_id, session)
            return self._reply(next_step["prompt"], list(_FLOW_QUICK_REPLIES), session["state"], flow_id)

        return self._complete_flow(session_id, session, flow_id, flow)

    def _complete_flow(self, session_id, session, flow_id, flow):
        data = session["data"]
        resolver = flow.get("resolver")

        if resolver and resolver in self.resolvers:
            result = self.resolvers[resolver](data)
            if isinstance(result, dict):
                if result.get("retry"):
                    retry_step = result.get("step", flow["steps"][-1]["key"])
                    session["data"].pop(retry_step, None)
                    session["state"] = f"flow.{flow_id}.{retry_step}"
                    storage.save_session(session_id, session)
                    return self._reply(result.get("reply", ""), list(_FLOW_QUICK_REPLIES), session["state"], flow_id)
                reply_text = result.get("reply", "")
            else:
                reply_text = str(result)
        else:
            reply_text = flow.get("completion", "").format(**data)

        if flow.get("store") == "lead":
            storage.save_lead(session_id, data)

        storage.save_session(session_id, self._new_session())
        intent_id = f"{flow_id}_saved" if flow.get("store") else f"{flow_id}_done"
        return self._reply(reply_text, self._default_quick_replies(), "idle", intent_id)

    def _parse_flow_state(self, state):
        parts = state.split(".", 2)
        flow_id = parts[1] if len(parts) > 1 else ""
        step_key = parts[2] if len(parts) > 2 else ""
        return flow_id, step_key

    def _is_cancel(self, text, flow):
        lowered = text.strip().lower()
        return any(keyword in lowered for keyword in flow.get("cancel_keywords", []))

    def _validate(self, step, value):
        rule = step.get("validate", "nonempty")
        if rule == "name":
            if len(value) >= 2 and any(char.isalpha() for char in value):
                return None
            return step["error"]
        if rule == "phone":
            digits = _PHONE_RE.sub("", value)
            if 10 <= len(digits) <= 11:
                return None
            return step["error"]
        if not value:
            return step["error"]
        return None
