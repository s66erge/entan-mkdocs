import pytest
from unittest.mock import Mock
from fasthtml.common import database, to_xml
from libs.dbset import create_tables, init_data
from libs.utils import feed_text

from main import app
from libs.admin import ( show_users_table, show_users_form,
    show_centers_table, show_centers_form,
    show_planners_table, show_planners_form, show_page )

@pytest.fixture
def temp_db():
    "Create a temporary database in memory and initialize tables"
    db = database(":memory:")
    create_tables(db)
    init_data(db)
    yield db
    db.conn.close()

def test_show_users_table(temp_db):
    db = temp_db
    users = db.t.users
    User = users.dataclass()
    result = to_xml(show_users_table(users))
    assert users()[0].email in result
    assert "Email" in result
    assert "Name" in result
    assert "Role" in result
    assert "Active" in result
    assert "Action" in result

def test_show_users_table_sorted_by_name(temp_db):
    db = temp_db
    users = db.t.users
    users.insert(email="zuser@example.com", name="Zara User", role_name="user", is_active=False, magic_link_token=None, magic_link_expiry=None)
    users.insert(email="auser@example.com", name="Adam User", role_name="user", is_active=False, magic_link_token=None, magic_link_expiry=None)
    result = to_xml(show_users_table(users))
    # Adam should appear before Zara
    adam_pos = result.find("Adam User")
    zara_pos = result.find("Zara User")
    assert adam_pos < zara_pos

def test_show_users_form_has_all_roles(temp_db):
    db = temp_db
    roles = db.t.roles
    result = to_xml(show_users_form(roles))
    Role = roles.dataclass()
    for role in roles():
        assert role.role_name in result

def test_show_users_form(temp_db):
    db = temp_db
    roles = db.t.roles
    result = to_xml(show_users_form(roles))
    assert "User Email" in result
    assert "User full name" in result
    assert "Select Role" in result
    assert "Add User" in result
    assert "#users-feedback" in result

def test_show_centers_table_multiple_centers(temp_db):
    db = temp_db
    centers = db.t.centers
    centers.insert(center_name="Center A", location="123", gong_db_name="center_a.db", other_course="{}")
    centers.insert(center_name="Center Z", location="456", gong_db_name="center_b.db", other_course="{}")
    result = to_xml(show_centers_table(centers))
    assert "Center A" in result
    assert "Center Z" in result
    assert "center_a.db" in result
    assert "center_b.db" in result
    assert "Name" in result
    assert "Gong DB Name" in result
    assert "Actions" in result
    alpha_pos = result.find("Center A")
    zebra_pos = result.find("Center Z")
    assert alpha_pos < zebra_pos

def test_show_centers_form(temp_db):
    db = temp_db
    centers = db.t.centers
    centers.insert(center_name="Test Center", location="789", gong_db_name="test.db", other_course="{}")
    result = to_xml(show_centers_form(centers))
    assert "Center Name" in result
    assert "Center location number" in result
    assert "Gong DB Name" in result
    assert "Center planning to copy" in result
    assert "Add Center" in result
    assert "test.db" in result
    assert "#centers-feedback" in result

def test_show_planners_table_sorted_by_center(temp_db):
    db = temp_db
    centers = db.t.centers
    users = db.t.users
    planners = db.t.planners
    centers.insert(center_name="Zebra Center", location="999", gong_db_name="zebra.db", other_course="{}")
    centers.insert(center_name="Alpha Center", location="111", gong_db_name="alpha.db", other_course="{}")
    users.insert(email="p1@example.com", name="Planner 1", role_name="user", is_active=False, magic_link_token=None, magic_link_expiry=None)
    users.insert(email="p2@example.com", name="Planner 2", role_name="user", is_active=False, magic_link_token=None, magic_link_expiry=None)
    planners.insert(user_email="p1@example.com", center_name="Zebra Center")
    planners.insert(user_email="p2@example.com", center_name="Alpha Center")
    result = to_xml(show_planners_table(planners))
    assert "p1@example.com" in result
    assert "User Email" in result
    assert "Center Name" in result
    assert "Actions" in result
    alpha_pos = result.find("Alpha Center")
    zebra_pos = result.find("Zebra Center")
    assert alpha_pos < zebra_pos

def test_show_planners_form_sorted(temp_db):
    db = temp_db
    users = db.t.users
    centers = db.t.centers
    users.insert(email="z@example.com", name="Zoe", role_name="user", is_active=False, magic_link_token=None, magic_link_expiry=None)
    users.insert(email="a@example.com", name="Alice", role_name="user", is_active=False, magic_link_token=None, magic_link_expiry=None)
    centers.insert(center_name="Zebra", location="999", gong_db_name="zebra.db", other_course="{}")
    centers.insert(center_name="Alpha", location="111", gong_db_name="alpha.db", other_course="{}")
    result = to_xml(show_planners_form(users, centers))
    # Check users are sorted by name
    alice_pos = result.find("a@example.com")
    zoe_pos = result.find("z@example.com")
    assert alice_pos < zoe_pos
    # Check centers are sorted by name
    alpha_pos = result.find("Alpha")
    zebra_pos = result.find("Zebra")
    assert alpha_pos < zebra_pos

def test_show_page(temp_db):
    "Test show_page renders all admin sections."
    db = temp_db
    users = db.t.users
    centers = db.t.centers
    planners = db.t.planners
    # Add test data
    users.insert(email="admin@example.com", name="Admin User", role_name="user", is_active=True, magic_link_token=None, magic_link_expiry=None)
    centers.insert(center_name="Test Center", location="100", gong_db_name="test.db", other_course="{}")
    planners.insert(user_email="admin@example.com", center_name="Test Center")
    # Create mock request with empty query params
    request = Mock()
    request.query_params = {}
    result = to_xml(show_page(request, db))
    # Check navigation elements
    assert "Dashboard" in result
    assert "Contact" in result
    assert "About" in result
    assert "Logout" in result
    # Check main sections
    assert "Users" in result
    assert "Centers" in result
    assert "Planners" in result
    # Check tables
    assert "users-table" in result
    assert "centers-table" in result
    assert "planners-table" in result
    # Check forms
    assert "users-form" in result
    assert "centers-form" in result
    assert "planners-form" in result
    # Check feedback divs
    assert "users-feedback" in result
    assert "centers-feedback" in result
    assert "planners-feedback" in result
    # Check data appears in result
    assert "admin@example.com" in result
    assert "Admin User" in result
    assert "Test Center" in result
    assert "test.db" in result

def test_show_page_with_feedback_params(temp_db):
    "Test show_page with feedback parameters in query."
    feedback = {"success": "user_added"}
    message = feed_text(feedback)["mess"]
    db = temp_db
    request = Mock()
    request.query_params = feedback
    result = to_xml(show_page(request, db))
    # Check feedback is displayed
    assert message in result
