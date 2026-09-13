import random
import re

from . import storage
from .nlu import lemmatize

_PHONE_RE = re.compile(r"\D")


class DialogEngine:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self._index = self._build_index()
        self.threshold = float(self.kb.settings.get("match_threshold", 1.0))

    def _build_index(self):
        index = []
        for intent in self.kb.intents:
            patterns = []
            for keyword in intent.get("keywords", []):
                lemmas = frozenset(lemmatize(keyword))
                if lemmas:
                    patterns.append((lemmas, len(lemmas)))
            index.append((intent, patterns))
        return index

    def detect_intent(self, text):
        message_lemmas = set(lemmatize(text))
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
        return {"state": "idle", "lead": {}}

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

    def _reset_reply(self, session_id, message):
        storage.save_session(session_id, self._new_session())
        return self._reply(message, self._default_quick_replies(), "idle", "reset")

    def process(self, session_id, text):
        session = storage.get_session(session_id) or self._new_session()
        flow = self.kb.flows.get("lead")

        command = self._parse_command(text)
        if command in ("start", "reset", "restart"):
            return self._reset_reply(session_id, self.welcome())
        if command in ("help",):
            return self._reply(self.help_text(), self._default_quick_replies(), "idle", "help")

        state = session.get("state", "idle")
        if flow and state.startswith("lead."):
            return self._handle_lead(session_id, session, text, flow)

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

        if flow and intent["id"] == flow.get("trigger"):
            first_step = flow["steps"][0]
            session = self._new_session()
            session["state"] = f"lead.{first_step['key']}"
            storage.save_session(session_id, session)
            return self._reply(first_step["prompt"], [], session["state"], intent["id"])

        replies = intent.get("responses") or ["Пока не могу ответить на это."]
        quick_replies = intent.get("quick_replies")
        if quick_replies is None:
            quick_replies = self._default_quick_replies()
        return self._reply(random.choice(replies), list(quick_replies), "idle", intent["id"])

    def _handle_lead(self, session_id, session, text, flow):
        if self._is_cancel(text, flow):
            session = self._new_session()
            storage.save_session(session_id, session)
            return self._reply(
                "Хорошо, отменил заявку. Чем ещё могу помочь?",
                self._default_quick_replies(),
                "idle",
                "lead_cancel",
            )

        step_key = session["state"].split(".", 1)[1]
        step = next((item for item in flow["steps"] if item["key"] == step_key), None)
        if step is None:
            storage.save_session(session_id, self._new_session())
            return self._reply("Что-то пошло не так. Начнём заново.", self._default_quick_replies(), "idle")

        value = text.strip()
        error = self._validate(step, value)
        if error:
            return self._reply(error, [], session["state"], "lead")

        session["lead"][step_key] = value
        index = flow["steps"].index(step)

        if index + 1 < len(flow["steps"]):
            next_step = flow["steps"][index + 1]
            session["state"] = f"lead.{next_step['key']}"
            storage.save_session(session_id, session)
            return self._reply(next_step["prompt"], [], session["state"], "lead")

        lead = session["lead"]
        storage.save_lead(session_id, lead)
        storage.save_session(session_id, self._new_session())
        completion = flow["completion"].format(**lead)
        return self._reply(completion, self._default_quick_replies(), "idle", "lead_saved")

    def _is_cancel(self, text, flow):
        lowered = text.strip().lower()
        for keyword in flow.get("cancel_keywords", []):
            if keyword in lowered:
                return True
        return False

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
