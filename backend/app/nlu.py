import re

import pymorphy3

_morph = pymorphy3.MorphAnalyzer()
_clean_re = re.compile(r"[^a-zа-я0-9\s\-]", re.IGNORECASE)
_space_re = re.compile(r"\s+")


def _normalize(text):
    lowered = text.lower().replace("ё", "е")
    cleaned = _clean_re.sub(" ", lowered)
    return _space_re.sub(" ", cleaned).strip()


def lemmatize(text):
    result = []
    for token in _normalize(text).split():
        parts = [part for part in token.split("-") if part]
        if not parts:
            continue
        result.append("-".join(_morph.parse(part)[0].normal_form for part in parts))
    return result


def lemma_set(text):
    return set(lemmatize(text))
