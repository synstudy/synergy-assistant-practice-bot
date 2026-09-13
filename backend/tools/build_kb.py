import argparse
import json
from pathlib import Path

from .md_to_kb import build_intents, parse_markdown

BASE = Path(__file__).resolve().parents[1]

GENERIC_LEMMAS = {
    "обучение", "образование", "развитие", "деятельность", "структура", "состав",
    "фактор", "проект", "программа", "данные", "информация", "сведение",
    "характеристика", "уровень", "оценка", "система", "компания", "страна",
    "место", "часть", "значение", "работа",
}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def dedupe(items):
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def _lemma_set(text):
    from app.nlu import lemma_set

    return lemma_set(text)


def filter_keywords(keywords):
    result = []
    for keyword in keywords:
        lemmas = _lemma_set(keyword)
        if len(lemmas) >= 2:
            result.append(keyword)
        elif lemmas and next(iter(lemmas)) not in GENERIC_LEMMAS:
            result.append(keyword)
    return result


def build_target(entry, base=BASE):
    source = base / entry["source"]
    overlay = load_json(base / entry["overlay"])
    generated = build_intents(
        parse_markdown(source.read_text(encoding="utf-8")),
        min_level=entry.get("min_level", 2),
    )

    overrides = overlay.get("keyword_overrides", {})
    for intent in generated:
        intent.pop("quick_replies", None)
        intent["keywords"] = filter_keywords(intent["keywords"])
        extras = overrides.get(intent["id"])
        if extras:
            intent["keywords"] = dedupe(intent["keywords"] + extras)

    return {
        "meta": overlay.get("meta", {}),
        "settings": overlay.get("settings", {}),
        "fallback": overlay.get("fallback", {}),
        "intents": list(overlay.get("intents", [])) + generated,
        "flows": overlay.get("flows", {}),
    }


def render(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def main():
    parser = argparse.ArgumentParser(
        description="Сборка баз знаний из sources/ и overlay-файлов."
    )
    parser.add_argument("--config", default="kb/config.json", help="путь к config.json")
    parser.add_argument("--check", action="store_true", help="проверить расхождение с sources, не записывая")
    args = parser.parse_args()

    config = load_json(BASE / args.config)
    exit_code = 0

    for entry in config["targets"]:
        data = build_target(entry)
        payload = render(data)
        target = BASE / entry["target"]

        if args.check:
            current = target.read_text(encoding="utf-8") if target.exists() else ""
            if current != payload:
                print(f"РАСХОЖДЕНИЕ: {entry['target']}")
                exit_code = 1
            else:
                print(f"OK: {entry['target']}")
        else:
            target.write_text(payload, encoding="utf-8")
            print(f"Готово: {entry['target']} — {len(data['intents'])} интентов")

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
