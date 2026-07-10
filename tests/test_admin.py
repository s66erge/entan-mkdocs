from unittest.mock import Mock

from fasthtml.common import to_xml

from libs.messages import feed_text
from libs.admin import (
    show_users_table, show_users_form,
    show_centers_table, show_centers_form,
    show_planners_table, show_planners_form, show_page,
)

from tests.conftest import add_center_row, add_user_row


def test_show_users_table(tables):
    _, _, users, _, _ = tables
    result = to_xml(show_users_table(users))
    assert users()[0].email in result
    for header in ("Email", "Name", "Role", "Active", "Action"):
        assert header in result


def test_show_users_table_sorted_by_name(tables):
    _, _, users, _, _ = tables
    add_user_row(users, "zuser@example.com", "Zara User")
    add_user_row(users, "auser@example.com", "Adam User")
    result = to_xml(show_users_table(users))
    assert result.find("Adam User") < result.find("Zara User")


def test_show_users_form_has_all_roles(tables):
    _, roles, _, _, _ = tables
    result = to_xml(show_users_form(roles))
    for role in roles():
        assert role.role_name in result


def test_show_users_form(tables):
    _, roles, _, _, _ = tables
    result = to_xml(show_users_form(roles))
    for text in ("User Email", "User full name", "Select Role", "Add User", "#users-feedback"):
        assert text in result


def test_show_centers_table(tables):
    _, _, _, centers, _ = tables
    add_center_row(centers, "Center A")
    add_center_row(centers, "Center Z")
    result = to_xml(show_centers_table(centers))
    assert "Center A" in result
    assert "Center Z" in result
    for header in ("Name", "status", "current user", "Actions"):
        assert header in result
    assert result.find("Center A") < result.find("Center Z")


def test_show_centers_form(tables):
    _, _, _, centers, _ = tables
    result = to_xml(show_centers_form(centers))
    for text in ("Center Name", "Center planning and config to copy", "Add Center", "#centers-feedback"):
        assert text in result
    # seeded centers appear as templates to copy from
    assert "Mahi" in result


def test_show_planners_table_sorted_by_center(tables):
    _, _, users, centers, planners = tables
    add_center_row(centers, "Zebra Center")
    add_center_row(centers, "Alpha Center")
    add_user_row(users, "p1@example.com", "Planner 1")
    add_user_row(users, "p2@example.com", "Planner 2")
    planners.insert(user_email="p1@example.com", center_name="Zebra Center")
    planners.insert(user_email="p2@example.com", center_name="Alpha Center")
    result = to_xml(show_planners_table(planners))
    assert "p1@example.com" in result
    for header in ("User Email", "Center Name", "Actions"):
        assert header in result
    assert result.find("Alpha Center") < result.find("Zebra Center")


def test_show_planners_form_sorted(tables):
    _, _, users, centers, _ = tables
    add_user_row(users, "z@example.com", "Zoe")
    add_user_row(users, "a@example.com", "Alice")
    add_center_row(centers, "Zebra")
    add_center_row(centers, "Alpha")
    result = to_xml(show_planners_form(users, centers))
    assert result.find("a@example.com") < result.find("z@example.com")
    assert result.find("Alpha") < result.find("Zebra")


def test_show_page(tables):
    _, roles, users, centers, planners = tables
    add_user_row(users, "admin2@example.com", "Admin User", is_active=True)
    add_center_row(centers, "Test Center")
    planners.insert(user_email="admin2@example.com", center_name="Test Center")
    request = Mock()
    request.query_params = {}
    result = to_xml(show_page(request, users, roles, centers, planners))
    for text in (
        "Dashboard", "About", "Contact", "Logout",
        "Users", "Centers", "Planners",
        "users-table", "centers-table", "planners-table",
        "users-form", "centers-form", "planners-form",
        "users-feedback", "centers-feedback", "planners-feedback",
        "admin2@example.com", "Admin User", "Test Center",
    ):
        assert text in result


def test_show_page_with_feedback_params(tables):
    _, roles, users, centers, planners = tables
    feedback = {"success": "user_added"}
    message = feed_text(feedback)["mess"]
    request = Mock()
    request.query_params = feedback
    result = to_xml(show_page(request, users, roles, centers, planners))
    assert message in result
