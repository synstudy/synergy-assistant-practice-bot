import os
import re
import threading
from functools import lru_cache

_LOCK = threading.Lock()
CONTENT_POS = {"NOUN", "PROPN", "VERB", "ADJ", "ADV", "NUM"}
CITY_LABELS = {"LOC", "GPE"}
_HYPHENS = {"-", "–", "—"}
_SPACE_RE = re.compile(r"\s+")
_HYPHEN_SPACE_RE = re.compile(r"\s*-\s*")


def enabled():
    value = os.environ.get("SPACY_ENABLED", "false").strip().lower()
    return value in ("1", "true", "yes", "on")


def matching_enabled():
    raw = os.environ.get("SPACY_MATCHING")
    if raw is None:
        return enabled()
    return raw.strip().lower() in ("1", "true", "yes", "on")


def model_name():
    return os.environ.get("SPACY_MODEL", "ru_core_news_sm").strip() or "ru_core_news_sm"


@lru_cache(maxsize=1)
def get_nlp():
    import spacy

    return spacy.load(model_name())


def _doc(text):
    with _LOCK:
        return get_nlp()(text)


def content_lemmas(text):
    doc = _doc(text)
    lemmas = {
        token.lemma_.lower()
        for token in doc
        if token.pos_ in CONTENT_POS and token.lemma_.strip()
    }
    if lemmas:
        return lemmas
    return {token.lemma_.lower() for token in doc if token.lemma_.strip()}


def entities(text):
    return [(entity.text, entity.label_) for entity in _doc(text).ents]


def _titlecase(name):
    words = []
    for word in name.split(" "):
        parts = [part[:1].upper() + part[1:] for part in word.split("-") if part]
        if parts:
            words.append("-".join(parts))
    return " ".join(words)


def _canonical_city(entity):
    parts = []
    for token in entity:
        if token.is_punct and token.text.strip() in _HYPHENS:
            parts.append("-")
        elif token.lemma_.strip():
            parts.append(token.lemma_.strip().lower())
    raw = _SPACE_RE.sub(" ", " ".join(parts)).strip()
    raw = _HYPHEN_SPACE_RE.sub("-", raw)
    return _titlecase(raw)


def city_from_text(text):
    for entity in _doc(text).ents:
        if entity.label_ in CITY_LABELS:
            city = _canonical_city(entity)
            if city:
                return city
    return None
