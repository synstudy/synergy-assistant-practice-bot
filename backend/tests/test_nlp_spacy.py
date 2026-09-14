from app import nlp_spacy


class FakeToken:
    def __init__(self, text, lemma, pos, is_punct=False):
        self.text = text
        self.lemma_ = lemma
        self.pos_ = pos
        self.is_space = False
        self.is_punct = is_punct


class FakeSpan:
    def __init__(self, text, label, tokens=()):
        self.text = text
        self.label_ = label
        self._tokens = list(tokens)

    def __iter__(self):
        return iter(self._tokens)


class FakeDoc:
    def __init__(self, tokens, ents=()):
        self._tokens = tokens
        self.ents = list(ents)

    def __iter__(self):
        return iter(self._tokens)


def _loc(text, tokens):
    return FakeDoc(tokens, ents=[FakeSpan(text, "LOC", tokens)])


DOCS = {
    "какой город": FakeDoc([FakeToken("Какой", "какой", "DET"), FakeToken("город", "город", "NOUN")]),
    "кто ты": FakeDoc([FakeToken("кто", "кто", "PRON"), FakeToken("ты", "ты", "PRON")]),
    "погода в Питере": _loc("Питере", [FakeToken("Питере", "питер", "PROPN")]),
    "какая погода в Москве?": _loc("Москве", [FakeToken("Москве", "москва", "PROPN")]),
    "погода в Нижнем Новгороде": _loc(
        "Нижнем Новгороде",
        [FakeToken("Нижнем", "нижний", "ADJ"), FakeToken("Новгороде", "новгород", "PROPN")],
    ),
    "погода в Санкт-Петербурге": _loc(
        "Санкт-Петербурге",
        [
            FakeToken("Санкт", "санкт", "PROPN"),
            FakeToken("-", "-", "PUNCT", is_punct=True),
            FakeToken("Петербурге", "петербург", "PROPN"),
        ],
    ),
}


def fake_nlp(text):
    return DOCS.get(text, FakeDoc([FakeToken(text, text.lower(), "NOUN")]))


def test_content_lemmas_drops_function_words(monkeypatch):
    monkeypatch.setattr(nlp_spacy, "get_nlp", lambda: fake_nlp)
    assert nlp_spacy.content_lemmas("какой город") == {"город"}


def test_content_lemmas_falls_back_for_function_only(monkeypatch):
    monkeypatch.setattr(nlp_spacy, "get_nlp", lambda: fake_nlp)
    assert nlp_spacy.content_lemmas("кто ты") == {"кто", "ты"}


def test_city_from_text_canonicalizes_cases(monkeypatch):
    monkeypatch.setattr(nlp_spacy, "get_nlp", lambda: fake_nlp)
    assert nlp_spacy.city_from_text("погода в Питере") == "Питер"
    assert nlp_spacy.city_from_text("какая погода в Москве?") == "Москва"
    assert nlp_spacy.city_from_text("погода в Нижнем Новгороде") == "Нижний Новгород"
    assert nlp_spacy.city_from_text("погода в Санкт-Петербурге") == "Санкт-Петербург"


def test_city_from_text_without_entities(monkeypatch):
    monkeypatch.setattr(nlp_spacy, "get_nlp", lambda: fake_nlp)
    assert nlp_spacy.city_from_text("какой город") is None


def test_flags_from_env(monkeypatch):
    monkeypatch.delenv("SPACY_ENABLED", raising=False)
    monkeypatch.delenv("SPACY_MATCHING", raising=False)
    assert nlp_spacy.enabled() is False
    assert nlp_spacy.matching_enabled() is False

    monkeypatch.setenv("SPACY_ENABLED", "true")
    monkeypatch.delenv("SPACY_MATCHING", raising=False)
    assert nlp_spacy.enabled() is True
    assert nlp_spacy.matching_enabled() is True

    monkeypatch.setenv("SPACY_MATCHING", "false")
    assert nlp_spacy.matching_enabled() is False
