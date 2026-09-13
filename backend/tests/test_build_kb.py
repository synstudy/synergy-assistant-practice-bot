import json

from tools.build_kb import build_target, filter_keywords, render


def test_filter_keywords_drops_generic_single_words():
    result = filter_keywords(["обучения", "формы обучения", "ректор"])
    assert "обучения" not in result
    assert "формы обучения" in result
    assert "ректор" in result


def test_build_target_merges_overlay_and_generated(tmp_path):
    (tmp_path / "sources").mkdir()
    (tmp_path / "sources" / "doc.md").write_text(
        "# Документ\n## Раздел\n### 1.1. Название компании\nТекст раздела.\n",
        encoding="utf-8",
    )
    (tmp_path / "kb").mkdir()
    (tmp_path / "kb" / "overlay.json").write_text(
        json.dumps(
            {
                "meta": {"name": "Тест"},
                "settings": {"match_threshold": 1.0},
                "fallback": {"responses": ["не понял"]},
                "intents": [
                    {"id": "greeting", "keywords": ["привет"], "responses": ["здравствуйте"]}
                ],
                "flows": {"lead": {"trigger": "lead_request"}},
                "keyword_overrides": {"nazvanie-kompanii": ["фирма"]},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    entry = {"source": "sources/doc.md", "overlay": "kb/overlay.json", "min_level": 2}
    data = build_target(entry, base=tmp_path)

    ids = [intent["id"] for intent in data["intents"]]
    assert ids[0] == "greeting"
    assert "nazvanie-kompanii" in ids
    assert data["flows"]["lead"]["trigger"] == "lead_request"

    generated = next(i for i in data["intents"] if i["id"] == "nazvanie-kompanii")
    assert "фирма" in generated["keywords"]
    assert "quick_replies" not in generated


def test_render_is_valid_json():
    payload = render({"intents": [], "meta": {"name": "Синергия"}})
    assert payload.endswith("\n")
    assert "Синергия" in payload
    json.loads(payload)
