import os
import tempfile
from pathlib import Path

TEST_DB = Path(tempfile.gettempdir()) / "synergy_chatbot_test.db"
os.environ["DB_PATH"] = str(TEST_DB)
os.environ["REPLY_DELAY_MIN"] = "0"
os.environ["REPLY_DELAY_MAX"] = "0"

import pytest


@pytest.fixture(autouse=True)
def clean_db():
    if TEST_DB.exists():
        TEST_DB.unlink()
    from app import storage

    storage.init_db()
    yield
    if TEST_DB.exists():
        TEST_DB.unlink()
