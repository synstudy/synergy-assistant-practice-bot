from app import storage
from app.engine import build_engine

engine = build_engine()


def test_recipe_flow_known_dish():
    session_id = "recipe-known"
    storage.reset_session(session_id)

    step = engine.process(session_id, "Расскажи рецепт")
    assert step["state"] == "flow.recipe.dish"

    result = engine.process(session_id, "борщ")
    assert result["state"] == "idle"
    assert "свёкл" in result["reply"].lower()


def test_recipe_flow_unknown_dish_gives_advice():
    session_id = "recipe-unknown"
    storage.reset_session(session_id)

    engine.process(session_id, "Как приготовить?")
    result = engine.process(session_id, "жареные кактусы")
    assert result["state"] == "idle"
    assert "кактус" in result["reply"].lower()


def test_recipe_flow_cancel():
    session_id = "recipe-cancel"
    storage.reset_session(session_id)

    engine.process(session_id, "Расскажи рецепт")
    result = engine.process(session_id, "отмена")
    assert result["state"] == "idle"
    assert result["intent"] == "recipe_cancel"
