import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*$")
NUMBER_RE = re.compile(r"^\s*\d+(?:\.\d+)*[.)]?\s+")
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
MARK_RE = re.compile(r"(\*\*|__|`|\*|_)")
BULLET_RE = re.compile(r"^\s*[-*+]\s+")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?\s*$")
WORD_RE = re.compile(r"[а-яёa-z0-9][а-яёa-z0-9-]{2,}")

STOPWORDS = {
    "раздел", "общая", "общее", "общий", "основные", "основной", "характеристика",
    "сведения", "информация", "данные", "краткая", "краткое", "полное", "того",
    "также", "более", "менее", "кроме", "весь", "все", "вся", "это", "этот",
    "эта", "эти", "для", "или", "при", "над", "под", "без", "через", "между",
    "среди", "может", "можно", "надо", "есть", "были", "было", "будет", "как",
    "чем", "что", "чтобы", "кто", "кого", "где", "когда", "почему", "который",
    "которая", "которые", "которого", "свой", "свои", "своя", "них", "него",
    "нее", "себя", "себе", "они", "она", "оно", "его", "ему", "им", "их",
    "этом", "этой", "этого", "тем", "том", "той", "др", "другие", "прочие",
    "годы", "год", "руб", "млн", "млрд", "тыс",
}

SYNONYMS = {
    "университет": ["вуз", "синергия"],
    "образование": ["обучение", "учиться"],
    "программа": ["направление", "специальность"],
    "руководство": ["ректор", "директор", "проректор"],
    "адрес": ["где находится", "местонахождение"],
    "студент": ["обучающийся"],
    "технология": ["цифровизация", "it"],
    "искусственный": ["ии", "нейросеть"],
    "филиал": ["представительство", "отделение"],
    "компания": ["корпорация", "организация"],
    "структура": ["подразделение", "состав"],
    "поступление": ["приём", "абитуриент"],
    "стоимость": ["цена", "оплата"],
    "аккредитация": ["лицензия", "диплом"],
}

TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "h", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}

DEFAULT_BASE = {
    "meta": {
        "name": "Организация",
        "welcome": "Здравствуйте! Я виртуальный помощник. Задайте вопрос или оставьте заявку.",
    },
    "settings": {
        "match_threshold": 1.0,
        "default_quick_replies": ["О компании", "Оставить заявку"],
    },
    "fallback": {
        "responses": ["Не уверен, что понял вопрос. Попробуйте переформулировать."],
        "quick_replies": ["О компании", "Оставить заявку"],
    },
    "flows": {},
}


@dataclass
class Section:
    level: int
    title: str
    lines: list = field(default_factory=list)
    children: list = field(default_factory=list)


def parse_markdown(text):
    root = Section(level=0, title="")
    stack = [root]
    for raw in text.splitlines():
        match = HEADING_RE.match(raw)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            while stack and stack[-1].level >= level:
                stack.pop()
            node = Section(level=level, title=title)
            stack[-1].children.append(node)
            stack.append(node)
        else:
            stack[-1].lines.append(raw)
    return root


def strip_markup(text):
    text = LINK_RE.sub(r"\1", text)
    text = MARK_RE.sub("", text)
    return text.strip()


def clean_title(title):
    return NUMBER_RE.sub("", title).strip(" .:")


def clean_text(lines):
    output = []
    for raw in lines:
        line = raw.rstrip()
        if not line.strip() or TABLE_SEP_RE.match(line):
            continue
        if line.lstrip().startswith("|"):
            cells = [strip_markup(cell) for cell in line.strip().strip("|").split("|")]
            cells = [cell for cell in cells if cell]
            if cells:
                sentence = " — ".join(cells)
                if sentence[-1] not in ".!?:":
                    sentence += "."
                output.append(sentence)
            continue
        line = BULLET_RE.sub("", line)
        line = strip_markup(line)
        if line:
            output.append(line)
    return "\n".join(output)


def slugify(title):
    lowered = clean_title(title).lower().replace("«", " ").replace("»", " ")
    chars = []
    for char in lowered:
        if char in TRANSLIT:
            chars.append(TRANSLIT[char])
        elif char.isalnum() and ord(char) < 128:
            chars.append(char)
        elif char in " -/":
            chars.append("-")
    slug = re.sub(r"-+", "-", "".join(chars)).strip("-")
    return slug or "section"


def keywords_for(title):
    phrase = clean_title(title).lower()
    words = [word for word in WORD_RE.findall(phrase) if word not in STOPWORDS]
    keywords = [phrase] + words
    for word in words:
        keywords.extend(SYNONYMS.get(word, []))
    unique = []
    for keyword in keywords:
        keyword = keyword.strip()
        if keyword and keyword not in unique:
            unique.append(keyword)
    return unique


def make_intent(section, seen_ids):
    title = clean_title(section.title)
    base = slugify(title)
    intent_id = base
    counter = 2
    while intent_id in seen_ids:
        intent_id = f"{base}-{counter}"
        counter += 1
    seen_ids.add(intent_id)
    children = [clean_title(child.title) for child in section.children]
    return {
        "id": intent_id,
        "keywords": keywords_for(title),
        "responses": [clean_text(section.lines)],
        "quick_replies": children[:4],
    }


def build_intents(root, min_level=2):
    intents = []
    seen_ids = set()

    def walk(section):
        if section.level >= min_level and clean_text(section.lines):
            intents.append(make_intent(section, seen_ids))
        for child in section.children:
            walk(child)

    for child in root.children:
        walk(child)
    return intents


def convert(markdown_path, base_path=None, merge=False, min_level=2):
    markdown = Path(markdown_path).read_text(encoding="utf-8")
    generated = build_intents(parse_markdown(markdown), min_level=min_level)

    if base_path:
        base = json.loads(Path(base_path).read_text(encoding="utf-8"))
    else:
        base = json.loads(json.dumps(DEFAULT_BASE))

    if merge:
        existing = {intent["id"] for intent in base.get("intents", [])}
        merged = list(base.get("intents", []))
        merged.extend(intent for intent in generated if intent["id"] not in existing)
        base["intents"] = merged
    else:
        base["intents"] = generated
    return base


def main():
    parser = argparse.ArgumentParser(
        description="Преобразование структурированного Markdown в базу знаний чат-бота."
    )
    parser.add_argument("markdown", help="путь к исходному .md файлу")
    parser.add_argument("-o", "--output", default="-", help="куда записать JSON (по умолчанию stdout)")
    parser.add_argument("--base", help="базовый knowledge_base.json (сохраняет settings/fallback/flows)")
    parser.add_argument("--merge", action="store_true", help="добавить интенты к базовым, не перезаписывая")
    parser.add_argument("--min-level", type=int, default=2, help="минимальный уровень заголовка (по умолчанию 2)")
    args = parser.parse_args()

    data = convert(args.markdown, args.base, args.merge, args.min_level)
    payload = json.dumps(data, ensure_ascii=False, indent=2)

    if args.output == "-":
        print(payload)
    else:
        Path(args.output).write_text(payload + "\n", encoding="utf-8")
        print(f"Готово: {len(data['intents'])} интентов → {args.output}")


if __name__ == "__main__":
    main()
