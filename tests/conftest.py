import pytest
from benchbro.db.schema import init_db


@pytest.fixture
async def db(tmp_path):
    db_path = tmp_path / "test.db"
    conn = await init_db(db_path)
    yield conn
    await conn.close()
