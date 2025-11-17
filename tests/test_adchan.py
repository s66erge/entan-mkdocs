import pytest
import tempfile
import os
from pathlib import Path
from libs.dbset import create_tables, init_data
from fasthtml.common import database

from libs.adchan import add_user, delete_user, add_center, delete_center, add_planner
from libs.feedb import *
from libs.admin import *


@pytest.fixture
def temp_db():
    "Create a temporary database in memory"
    db = database(":memory:")
    create_tables(db)
    init_data(db)
    yield db, "data/"
    db.conn.close()

@pytest.fixture
def clean_files():
    "Delete temporary db gong files"
    folder = "tests/data/"
    yield folder
    for filename in os.listdir(folder):
        if not filename.endswith(".ok.db"):
            file_path = os.path.join(folder, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)

def test_add_user_success(temp_db):
    "Test successfully adding a new user."
    db, _ = temp_db
    result = add_user("newuser@example.com", "John Doe", "user", db)
    result_str = str(result)
    assert "success" in result_str
    # Check user was added
    users = db.t.users
    User= users.dataclass()
    user = users("email = ?", ("newuser@example.com",))
    assert len(user) == 1
    assert user[0].name == "John Doe"
    assert user[0].role_name == "user"
    assert user[0].is_active == False

def test_add_user_missing_fields(temp_db):
    "Test adding user with missing fields."
    db, _ = temp_db
    add_user("newuser@example.com", "John Doe", "", db)
    users = db.t.users
    assert len(users()) == 2  # No new user added

def test_add_user_invalid_role(temp_db):
    "Test adding user with invalid role."
    db, _ = temp_db
    add_user("newuser@example.com", "John Doe", "InvalidRole", db)
    # Check user was not added
    users = db.t.users
    user = users("email = ?", ("newuser@example.com",))
    assert len(user) == 0

def test_add_user_already_exists(temp_db):
    "Test adding user that already exists."
    db, _ = temp_db
    # Add first user
    add_user("existing@example.com", "Jane Doe", "admin", db)
    # Try to add same user again
    result = add_user("existing@example.com", "Another Name", "user", db)
    # Check only one user exists with that email
    users = db.t.users
    User= users.dataclass()
    user = users("email = ?", ("existing@example.com",))
    assert len(user) == 1
    assert user[0].name == "Jane Doe"  # Original name preserved

def test_delete_user_not_found(temp_db):
    "Deleting a non-existent user returns user_not_found error."
    db, _ = temp_db
    result = delete_user("noone@example.com", db)
    assert isinstance(result, dict)
    assert result.get("error") == "user_not_found"

def test_delete_user_has_planners(temp_db, clean_files):
    "Deleting a user that has planner associations returns error with centers listed."
    db, _ = temp_db
    ffolder = clean_files
    users = db.t.users
    centers = db.t.centers
    planners = db.t.planners
    Center = centers.dataclass()
    Planner = planners.dataclass()
    User = users.dataclass()
    # create center, user and planner association
    center_name = "TestCenter"
    add_center(center_name, "laba", "tc.db", "mahi.ok.db", db, ffolder)
    email = "planner@example.com"
    add_user(email, "Planner", "user", db)
    planners.insert(user_email=email, center_name=center_name)
    result = delete_user(email, db)
    assert isinstance(result, dict)
    assert result.get("error") == "user_has_planners"
    assert center_name in result.get("centers", "")

def test_delete_user_success(temp_db):
    "Successfully delete a user with no planner associations."
    db, _ = temp_db
    email = "todelete@example.com"
    add_user(email, "To Delete", "user", db)
    result = delete_user(email, db)
    assert isinstance(result, dict)
    assert result.get("success") == "user_deleted"
    # verify removal from users table
    remaining = db.t.users("email = ?", (email,))
    assert len(remaining) == 0

def test_add_center_success(temp_db, clean_files):
    "Test successfully adding a new center."
    db, _ = temp_db
    ffolder = clean_files
    centers = db.t.centers
    Center = centers.dataclass()
    result = add_center("NewCenter", "New Location", "new_center.db",
                        "mahi.ok.db", db, ffolder)
    result_str = str(result)
    assert "success" in result_str
    # Verify center was added
    center = centers("center_name = ?", ("NewCenter",))
    assert len(center) == 1
    assert center[0].location == "New Location"
    assert center[0].gong_db_name == "new_center.db"

def test_add_center_missing_fields(temp_db, clean_files):
    "Test adding center with missing required fields."
    db, _ = temp_db
    ffolder = clean_files
    centers = db.t.centers
    add_center("", "Location", "db.db", "mahi.ok.db", db, ffolder)
    # Check that no center was added
    all_centers = centers()
    assert len(all_centers) == 2

def test_add_center_already_exists(temp_db, clean_files):
    "Test adding a center that already exists."
    db, _ = temp_db
    ffolder = clean_files
    centers = db.t.centers
    Center = centers.dataclass()
    # Add first center
    result = add_center("ExistingCenter", "Existing Location", "existing.db", "mahi.ok.db",
                        db, ffolder)
    # Try to add same center again
    result = add_center("ExistingCenter", "Different Location", "different.db", "mahi.ok.db",
                        db, ffolder)
    result_str = str(result)
    assert "error" in result_str or "exists" in result_str
    # Verify original center unchanged
    center = centers("center_name = ?", ("ExistingCenter",))
    assert len(center) == 1
    assert center[0].location == "Existing Location"
    assert center[0].gong_db_name == "existing.db"
    # clean up created gong db file

def test_add_center_invalid_template(temp_db, clean_files):
    "Test adding center with non-existent template."
    db, _ = temp_db
    ffolder = clean_files
    centers = db.t.centers
    result = add_center("TemplateTestCenter", "Template Test", "template_test.db",
                        "nonexistent_template.db", db, ffolder)
    # Should contain error about template
    assert 'template' in result.get("error") 
    # Verify center was not added
    center = centers("center_name = ?", ("TemplateTestCenter",))
    assert len(center) == 0

def test_add_center_duplicate_gong_db_name(temp_db, clean_files):
    "Test adding center with duplicate gong_db_name."
    db, _ = temp_db
    ffolder = clean_files
    centers = db.t.centers
    Center = centers.dataclass()
    # Add first center
    add_center("Center1", "Location 2", "shared.db", "mahi.ok.db", db, ffolder)
    # Try to add center with same gong_db_name
    result = add_center("Center2", "Location 2", "shared.db", "mahi.ok.db",
                        db, ffolder)
    result_str = str(result)
    assert "error" in result_str or "exists" in result_str.lower()
    # Verify only first center exists
    center = centers("center_name = ?", ("Center1",))
    assert len(center) == 1

def test_delete_center_not_found(temp_db, clean_files):
    "Deleting a non-existent center returns center_not_found error."
    db, _ = temp_db
    ffolder = clean_files
    result = delete_center("NonexistentCenter", db, ffolder)
    assert isinstance(result, dict)
    assert result.get("error") == "center_not_found"

def test_delete_center_has_planners(temp_db, clean_files):
    "Deleting a center that has planner associations returns error with users listed."
    db, _ = temp_db
    ffolder = clean_files
    centers = db.t.centers
    # Create center, user and planner association
    center_name = "CenterWithPlanners"
    add_center(center_name, "Location 2", "shared.db", "mahi.ok.db", db, ffolder)
    email = "planner1@example.com"
    add_user(email, "Planner One", "user", db)
    add_planner(email, center_name, db)
    result = delete_center(center_name, db, ffolder)
    assert isinstance(result, dict)
    assert result.get("error") == "center_has_planners"
    assert email in result.get("users", "")
    # Verify center was not deleted
    center = centers("center_name = ?", (center_name,))
    assert len(center) == 1

def test_delete_center_success(temp_db, clean_files):
    "Successfully delete a center with no planner associations."
    db, _ = temp_db
    db_path = clean_files
    centers = db.t.centers
    # First add a center
    add_center("CenterToDelete", "Delete Location", "delete_center.db", "mahi.ok.db",
               db, db_path)
    # Verify center was added
    center = centers("center_name = ?", ("CenterToDelete",))
    assert len(center) == 1
    # Delete the center
    result = delete_center("CenterToDelete", db, db_path)
    assert isinstance(result, dict)
    assert result.get("success") == "center_deleted"
    # Verify center is removed from database
    remaining = centers("center_name = ?", ("CenterToDelete",))
    assert len(remaining) == 0

def test_delete_center_removes_gong_db(temp_db, clean_files):
    "Verify that delete_center removes the gong database file."
    db, _ = temp_db
    db_path = clean_files
    centers = db.t.centers
    gong_db_name = "remove_me.db"
    # Add a center
    add_center("CenterWithDB", "DB Location", gong_db_name, "mahi.ok.db", db, db_path)
    # Verify gong database file exists
    db_file_path = os.path.join(db_path, gong_db_name)
    assert os.path.exists(db_file_path), f"Gong DB file not found at {db_file_path}"
    # Delete the center
    result = delete_center("CenterWithDB", db, db_path)
    assert result.get("success") == "center_deleted"
    # Verify gong database file is deleted
    assert not os.path.exists(db_file_path), f"Gong DB file still exists at {db_file_path}"    

def test_add_planner_success(temp_db, clean_files):
    "Test successfully adding a new planner."
    db, _ = temp_db
    ffolder = clean_files
    planners = db.t.planners
    # First create a center and user
    add_center("PlannerCenter", "Center Location", "planner.db", "mahi.ok.db", db, ffolder)
    add_user("planner@example.com", "Test Planner", "user", db)
    # Add planner association
    result = add_planner("planner@example.com", "PlannerCenter", db)
    result_str = str(result)
    assert "success" in result_str
    # Verify planner was added
    planner = planners("user_email = ? AND center_name = ?", ("planner@example.com", "PlannerCenter"))
    assert len(planner) == 1

def test_add_planner_missing_fields(temp_db, clean_files):
    "Test adding planner with missing required fields."
    db, _ = temp_db
    ffolder = clean_files
    planners = db.t.planners
    # Try to add planner with empty email
    result = add_planner("", "SomeCenter", db)
    result_str = str(result)
    assert "missing_fields" in result_str or "error" in result_str
    # Try to add planner with empty center
    result = add_planner("planner@example.com", "", db)
    result_str = str(result)
    assert "missing_fields" in result_str or "error" in result_str

def test_add_planner_user_not_found(temp_db, clean_files):
    "Test adding planner with non-existent user."
    db, _ = temp_db
    ffolder = clean_files
    # Create a center but no user
    add_center("TestCenter", "Location", "test.db", "mahi.ok.db", db, ffolder)
    result = add_planner("nonexistent@example.com", "TestCenter", db)
    assert isinstance(result, dict)
    assert result.get("error") == "user_not_found"


def test_add_planner_center_not_found(temp_db, clean_files):
    "Test adding planner with non-existent center."
    db, _ = temp_db
    # Create a user but no center
    add_user("planner@example.com", "Test Planner", "user", db)
    result = add_planner("planner@example.com", "NonexistentCenter", db)
    assert isinstance(result, dict)
    assert result.get("error") == "center_not_found"

def test_add_planner_already_exists(temp_db, clean_files):
    "Test adding a planner association that already exists."
    db, _ = temp_db
    ffolder = clean_files
    planners = db.t.planners
    # Create center and user
    add_center("ExistingCenter", "Location", "existing.db", "mahi.ok.db", db, ffolder)
    add_user("existing@example.com", "Existing Planner", "user", db)
    # Add planner first time
    add_planner("existing@example.com", "ExistingCenter", db)
    # Try to add same planner again
    result = add_planner("existing@example.com", "ExistingCenter", db)
    result_str = str(result)
    assert "error" in result_str or "exists" in result_str
    # Verify only one planner record exists
    planner = planners("user_email = ? AND center_name = ?", ("existing@example.com", "ExistingCenter"))
    assert len(planner) == 1

def test_add_planner_multiple_planners_same_center(temp_db, clean_files):
    "Test adding multiple planners to the same center."
    db, _ = temp_db
    ffolder = clean_files
    planners = db.t.planners
    # Create center
    add_center("SharedCenter", "Shared Location", "shared.db", "mahi.ok.db", db, ffolder)
    # Add multiple users and planners
    for i in range(3):
        email = f"planner{i}@example.com"
        add_user(email, f"Planner {i}", "user", db)
        result = add_planner(email, "SharedCenter", db)
        result_str = str(result)
        assert "success" in result_str
    # Verify all planners were added
    all_planners = planners("center_name = ?", ("SharedCenter",))
    assert len(all_planners) == 3

def test_add_planner_same_user_multiple_centers(temp_db, clean_files):
    "Test adding the same user as planner to multiple centers."
    db, _ = temp_db
    ffolder = clean_files
    planners = db.t.planners
    # Create user
    add_user("versatile@example.com", "Versatile Planner", "user", db)
    # Add multiple centers
    for i in range(3):
        add_center(f"Center{i}", f"Location {i}", f"center{i}.db", "mahi.ok.db", db, ffolder)
        result = add_planner("versatile@example.com", f"Center{i}", db)
        result_str = str(result)
        assert "success" in result_str
    # Verify all planner associations were added
    user_planners = planners("user_email = ?", ("versatile@example.com",))
    assert len(user_planners) == 3

