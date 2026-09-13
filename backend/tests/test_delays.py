from app import delays


def _clear(monkeypatch):
    monkeypatch.delenv("REPLY_DELAY_MIN", raising=False)
    monkeypatch.delenv("REPLY_DELAY_MAX", raising=False)


def test_defaults_within_range(monkeypatch):
    _clear(monkeypatch)
    value = delays.reply_delay()
    assert 2.0 <= value <= 4.0


def test_fixed_value(monkeypatch):
    monkeypatch.setenv("REPLY_DELAY_MIN", "1.5")
    monkeypatch.setenv("REPLY_DELAY_MAX", "1.5")
    assert delays.reply_delay() == 1.5


def test_disabled_with_zero_max(monkeypatch):
    monkeypatch.setenv("REPLY_DELAY_MIN", "2")
    monkeypatch.setenv("REPLY_DELAY_MAX", "0")
    assert delays.reply_delay() == 0.0


def test_swapped_bounds(monkeypatch):
    monkeypatch.setenv("REPLY_DELAY_MIN", "3")
    monkeypatch.setenv("REPLY_DELAY_MAX", "1")
    value = delays.reply_delay()
    assert 1.0 <= value <= 3.0


def test_invalid_values_fall_back_to_defaults(monkeypatch):
    monkeypatch.setenv("REPLY_DELAY_MIN", "abc")
    monkeypatch.setenv("REPLY_DELAY_MAX", "")
    value = delays.reply_delay()
    assert 2.0 <= value <= 4.0
