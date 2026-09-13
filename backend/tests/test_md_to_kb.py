from tools.md_to_kb import build_intents, clean_text, convert, parse_markdown, slugify

SAMPLE = """# Документ
Вводный текст, из которого интент не делаем.

## Раздел 1. О компании
### 1.1. Название компании
**Полное:** ООО «Ромашка».
### 1.2. Контакты
Телефон: +7 000 000-00-00.

| Город | Улица |
|---|---|
| Москва | Мещанская |
"""


def test_parse_builds_intents_from_leaf_sections():
    intents = build_intents(parse_markdown(SAMPLE), min_level=2)
    ids = [intent["id"] for intent in intents]
    assert "nazvanie-kompanii" in ids
    assert "kontakty" in ids
    assert "razdel-1-o-kompanii" not in ids


def test_table_is_converted_to_text():
    intents = build_intents(parse_markdown(SAMPLE), min_level=2)
    contacts = next(intent for intent in intents if intent["id"] == "kontakty")
    response = contacts["responses"][0]
    assert "Москва — Мещанская" in response
    assert "|" not in response


def test_keywords_include_title_words():
    intents = build_intents(parse_markdown(SAMPLE), min_level=2)
    contacts = next(intent for intent in intents if intent["id"] == "kontakty")
    assert "контакты" in contacts["keywords"]


def test_slugify_handles_cyrillic():
    assert slugify("1.2. Контакты") == "kontakty"
    assert slugify("Организационно-правовая форма") == "organizatsionno-pravovaya-forma"


def test_clean_text_removes_markup():
    assert clean_text(["**Жирный** и `код`"]) == "Жирный и код"


def test_convert_merges_with_base(tmp_path):
    base = tmp_path / "base.json"
    base.write_text(
        '{"intents": [{"id": "manual", "keywords": ["вручную"], "responses": ["ok"]}]}',
        encoding="utf-8",
    )
    markdown = tmp_path / "doc.md"
    markdown.write_text(SAMPLE, encoding="utf-8")

    result = convert(markdown, base_path=base, merge=True)
    ids = [intent["id"] for intent in result["intents"]]
    assert "manual" in ids
    assert "kontakty" in ids


def test_convert_without_base_uses_defaults(tmp_path):
    markdown = tmp_path / "doc.md"
    markdown.write_text(SAMPLE, encoding="utf-8")
    result = convert(markdown)
    assert result["intents"]
    assert "fallback" in result
    assert "settings" in result
