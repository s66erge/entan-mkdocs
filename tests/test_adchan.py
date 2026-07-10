"""Unit tests for the DB-only admin-change operations.

add_center / delete_center are intentionally not covered here: they depend on
minio object storage, the filesystem, and the live state-machine registry, so
they belong in an integration suite rather than these in-memory unit tests.

The `tables` fixture (see conftest.py) seeds:
  users:    spegoff@authentica.eu, spegoff@gmail.com (both admin)
  centers:  Mahi, Pajjota, Testx
  planners: authentica->{Mahi,Pajjota,Testx}, gmail->{Pajjota,Mahi}
"""
from fasthtml.common import to_xml

from libs.messages import feed_text
from libs.adchan import add_user, delete_user, add_planner, delete_planner


# ---------------------------------------------------------------- add_user
def test_add_user_success(tables):
    _, roles, users, centers, _ = tables
    message = feed_text({"success": "user_added"})["mess"]
    result = to_xml(add_user("newuser@example.com", "John Doe", "user", users, roles, centers))
    assert message in result
    user = users("email = ?", ("newuser@example.com",))
    assert len(user) == 1
    assert user[0].name == "John Doe"
    assert user[0].role_name == "user"
    assert not user[0].is_active  # stored as 0 in sqlite


def test_add_user_missing_fields(tables):
    _, roles, users, centers, _ = tables
    message = feed_text({"error": "missing_fields"})["mess"]
    result = to_xml(add_user("newuser@example.com", "John Doe", "", users, roles, centers))
    assert message in result
    assert len(users("email = ?", ("newuser@example.com",))) == 0


def test_add_user_invalid_role(tables):
    _, roles, users, centers, _ = tables
    message = feed_text({"error": "invalid_role"})["mess"]
    result = to_xml(add_user("newuser@example.com", "John Doe", "InvalidRole", users, roles, centers))
    assert message in result
    assert len(users("email = ?", ("newuser@example.com",))) == 0


def test_add_user_already_exists(tables):
    _, roles, users, centers, _ = tables
    message = feed_text({"error": "user_exists"})["mess"]
    add_user("existing@example.com", "Jane Doe", "admin", users, roles, centers)
    result = to_xml(add_user("existing@example.com", "Another Name", "user", users, roles, centers))
    assert message in result
    user = users("email = ?", ("existing@example.com",))
    assert len(user) == 1
    assert user[0].name == "Jane Doe"  # original preserved


# ---------------------------------------------------------------- delete_user
def test_delete_user_not_found(tables):
    _, _, users, centers, planners = tables
    message = feed_text({"error": "user_not_found"})["mess"]
    result = to_xml(delete_user("noone@example.com", users, planners, centers))
    assert message in result


def test_delete_user_has_planners(tables):
    _, _, users, centers, planners = tables
    message = feed_text({"error": "user_has_planners"})["mess"]
    # seeded user spegoff@authentica.eu is a planner for Mahi/Pajjota/Testx
    result = to_xml(delete_user("spegoff@authentica.eu", users, planners, centers))
    assert message.split(":")[0] in result
    assert "Mahi" in result
    # user still present
    assert len(users("email = ?", ("spegoff@authentica.eu",))) == 1


def test_delete_user_success(tables):
    _, roles, users, centers, planners = tables
    message = feed_text({"success": "user_deleted"})["mess"]
    add_user("todelete@example.com", "To Delete", "user", users, roles, centers)
    result = to_xml(delete_user("todelete@example.com", users, planners, centers))
    assert message in result
    assert len(users("email = ?", ("todelete@example.com",))) == 0


# ---------------------------------------------------------------- add_planner
def test_add_planner_success(tables):
    _, _, users, centers, planners = tables
    message = feed_text({"success": "planner_added"})["mess"]
    # gmail user is not yet a planner for Testx
    result = to_xml(add_planner("spegoff@gmail.com", "Testx", users, centers, planners))
    assert message in result
    assert len(planners("user_email = ? AND center_name = ?", ("spegoff@gmail.com", "Testx"))) == 1


def test_add_planner_missing_fields(tables):
    _, _, users, centers, planners = tables
    message = feed_text({"error": "missing_fields"})["mess"]
    assert message in to_xml(add_planner("", "Mahi", users, centers, planners))
    assert message in to_xml(add_planner("spegoff@gmail.com", "", users, centers, planners))


def test_add_planner_user_not_found(tables):
    _, _, users, centers, planners = tables
    message = feed_text({"error": "user_not_found"})["mess"]
    result = to_xml(add_planner("nonexistent@example.com", "Mahi", users, centers, planners))
    assert message in result


def test_add_planner_center_not_found(tables):
    _, _, users, centers, planners = tables
    result = to_xml(add_planner("spegoff@gmail.com", "NonexistentCenter", users, centers, planners))
    assert "not found" in result


def test_add_planner_already_exists(tables):
    _, _, users, centers, planners = tables
    message = feed_text({"error": "planner_exists"})["mess"]
    # gmail user is already a planner for Mahi
    result = to_xml(add_planner("spegoff@gmail.com", "Mahi", users, centers, planners))
    assert message in result
    assert len(planners("user_email = ? AND center_name = ?", ("spegoff@gmail.com", "Mahi"))) == 1


# ---------------------------------------------------------------- delete_planner
def test_delete_planner_last_planner(tables):
    _, _, _, _, planners = tables
    message = feed_text({"error": "last_planner_for_center"})["mess"]
    # Testx has exactly one planner (authentica) -> cannot delete the last one
    result = to_xml(delete_planner("spegoff@authentica.eu", "Testx", planners))
    assert message.split(":")[0] in result
    assert len(planners("center_name = ?", ("Testx",))) == 1


def test_delete_planner_success(tables):
    _, _, _, _, planners = tables
    message = feed_text({"success": "planner_deleted"})["mess"]
    # Mahi has two planners (authentica, gmail) -> deleting one succeeds
    result = to_xml(delete_planner("spegoff@gmail.com", "Mahi", planners))
    assert message in result
    assert len(planners("user_email = ? AND center_name = ?", ("spegoff@gmail.com", "Mahi"))) == 0
    assert len(planners("user_email = ? AND center_name = ?", ("spegoff@authentica.eu", "Mahi"))) == 1
