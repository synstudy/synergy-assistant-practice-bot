import argparse
import time

from app.dialog import DialogEngine
from app.knowledge import KnowledgeBase

CASES = [
    ("Привет", {"greeting"}),
    ("Здравствуйте", {"greeting"}),
    ("Что ты умеешь?", {"help", "chto-ty-umeesh"}),
    ("Какие у тебя возможности?", {"help"}),
    ("Начать заново", {"reset"}),
    ("Хочу записаться на консультацию", {"lead_request"}),
    ("Какая погода?", {"weather_general"}),
    ("Полное название университета", {"polnoe-i-sokraschennoe-ofitsialnoe-nazvanie"}),
    ("Какая правовая форма у вуза", {"organizatsionno-pravovaya-forma"}),
    ("Расскажи историю университета", {"istoriya-sozdaniya-i-klyuchevye-vehi"}),
    ("Есть ли лицензия", {"litsenziya-i-akkreditatsiya", "gosudarstvennye-litsenziya-i-akkreditatsiya"}),
    ("Какая миссия университета", {"missiya-i-pozitsionirovanie"}),
    ("Как добраться до главного офиса", {"yuridicheskiy-i-fakticheskiy-adres-golovnogo-ofisa"}),
    ("Сколько у вас филиалов", {"regionalnaya-set"}),
    ("Есть кампус в Дубае", {"mezhdunarodnoe-prisutstvie", "kampus-v-dubae-oae"}),
    ("Какие компании входят в корпорацию", {"korporatsiya-sinergiya-obschaya-struktura"}),
    ("Какие органы управления", {"organy-upravleniya-universitetom"}),
    ("Кто президент", {"prezident-universiteta"}),
    ("Кто ректор", {"rektor-universiteta"}),
    ("Функции ректора", {"funktsii-rektora"}),
    ("Структурные подразделения", {"fakultety-i-strukturnye-podrazdeleniya"}),
    ("Какие уровни образования", {"urovni-obrazovaniya"}),
    ("Сколько всего программ", {"obschee-chislo-obrazovatelnyh-programm", "kolichestvo-programm"}),
    ("Какие специальности есть", {"napravleniya-podgotovki-po-dannym-rosobrnadzora"}),
    ("Популярные программы", {"populyarnye-programmy"}),
    ("Онлайн обучение", {"onlayn-obuchenie", "formy-obucheniya", "formy-obucheniya-2"}),
    ("Сколько студентов", {"chislennost-studentov"}),
    ("Какие цифровые платформы", {"sobstvennye-tsifrovye-platformy"}),
    ("Используете нейросети", {"iskusstvennyy-intellekt"}),
    ("Выручка университета", {"finansovye-pokazateli"}),
    ("Сколько сотрудников", {"kadrovyy-sostav"}),
    ("Расскажи про мероприятия", {"obschestvennye-proekty"}),
    ("Судебные дела", {"sudebnye-dela-i-zadolzhennosti"}),
    ("Стоимость обучения", {"stoimost-za-semestr"}),
    ("Есть рассрочка", {"rassrochka-na-obuchenie"}),
    ("Образовательный кредит", {"kredit-na-obrazovanie-s-gospodderzhkoy"}),
    ("Какие скидки", {"skidki-i-spetsialnye-usloviya"}),
    ("Как поступить", {"kak-postupit"}),
    ("Есть бюджетные места", {"byudzhetnye-mesta"}),
    ("Дополнительные баллы", {"individualnye-dostizheniya-i-dopolnitelnye-bally"}),
    ("Перевод из другого вуза", {"perevod-iz-drugogo-vuza"}),
    ("Гарантия трудоустройства", {"garantiya-trudoustroystva"}),
    ("Центр карьеры", {"tsentr-karery"}),
    ("Компании партнеры", {"kompanii-partnery"}),
    ("Какие у вас рейтинги", {"rossiyskie-reytingi"}),
    ("Талисман университета", {"talisman-universiteta"}),
]

OOD = [
    "Рецепт борща",
    "Какой город считается столицей Австралии",
    "Погода на Марсе",
    "Купи билет на поезд",
    "Переведи текст на английский",
    "Сколько будет 2+2",
    "Кто написал Войну и мир",
    "Посоветуй фильм на вечер",
    "Как приготовить пасту",
    "Где купить телефон",
    "Расскажи анекдот про кота",
    "Что такое квантовая физика",
    "Расписание автобусов",
    "Закажи пиццу",
    "Который час в Нью-Йорке",
    "Кто выиграл чемпионат мира",
    "Как сбросить пароль Windows",
    "Сколько лет Луне",
    "Переведи на немецкий",
    "Дай совет по инвестициям",
]


def evaluate(engine):
    hits = 0
    misses = []
    for phrase, expected in CASES:
        intent, score = engine.detect_intent(phrase)
        got = intent["id"] if intent else None
        if got in expected:
            hits += 1
        else:
            misses.append((phrase, sorted(expected), got, score))

    false_positives = []
    for phrase in OOD:
        intent, score = engine.detect_intent(phrase)
        if intent:
            false_positives.append((phrase, intent["id"], score))

    return hits, misses, false_positives


def main():
    parser = argparse.ArgumentParser(description="Оценка качества распознавания интентов.")
    parser.add_argument("--latency", type=int, default=2000, help="число итераций для замера скорости")
    args = parser.parse_args()

    engine = DialogEngine(KnowledgeBase.load())
    hits, misses, false_positives = evaluate(engine)

    total = len(CASES)
    print(f"spacy_matching: {engine.spacy_matching}")
    print(f"Тематические фразы: {hits}/{total} = {hits / total:.1%}")
    print(f"Ложные срабатывания: {len(false_positives)}/{len(OOD)} = {len(false_positives) / len(OOD):.1%}")

    if misses:
        print("\nПромахи:")
        for phrase, expected, got, score in misses:
            print(f"  {phrase!r}: ожидался {expected}, получен {got} (score={score})")

    if false_positives:
        print("\nЛожные срабатывания:")
        for phrase, got, score in false_positives:
            print(f"  {phrase!r} -> {got} (score={score})")

    if args.latency > 0:
        start = time.perf_counter()
        for _ in range(args.latency):
            engine.detect_intent("Сколько стоит обучение в университете Синергия?")
        per_call = (time.perf_counter() - start) / args.latency
        print(f"\nСреднее время распознавания: {per_call * 1000:.2f} мс")


if __name__ == "__main__":
    main()
