import pytest
from fasthtml.common import database, to_xml
from libs.dbset import create_tables, init_data

from main import app
from libs.admin import show_users_table

@pytest.fixture
def temp_db():
    "Create a temporary database in memory and iniyialize tables"
    db = database(":memory:")
    create_tables(db)
    init_data(db)
    yield db
    db.conn.close()

def test_show_users_table(capfd, temp_db):
    db = temp_db
    users = db.t.users
    result = to_xml(show_users_table(users))
    assert "spegoff@gmail.com" in result
    # print(result)


