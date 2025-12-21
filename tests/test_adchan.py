import pytest
import os
from pathlib import Path
from libs.dbset import create_tables, init_data
from libs.utils import feed_text
from fasthtml.common import database, to_xml

from libs.adchan import add_user, delete_user, add_center, delete_center, add_planner, delete_planner


@pytest.fixture
def temp_db():
    "Create a temporary database in memory and initialize tables"
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
    message = feed_text({"success": "user_added"})["mess"]
    db, _ = temp_db
    result = add_user("newuser@example.com", "John Doe", "user", db)
    result_str = to_xml(result)
    assert message in result_str
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
    message = feed_text({"error" : "missing_fields"})["mess"]
    db, _ = temp_db
    result = add_user("newuser@example.com", "John Doe", "", db)
    result_str = to_xml(result)
    assert message in result_str
    users = db.t.users
    auser = users("email = ?", ("newuser@example.com",))
    assert len(auser) == 0  # No new user added

def test_add_user_invalid_role(temp_db):
    "Test adding user with invalid role."
    message = feed_text({"error": "invalid_role"})["mess"]
    db, _ = temp_db
    result = add_user("newuser@example.com", "John Doe", "InvalidRole", db)
    result_str = to_xml(result)
    assert message in result_str
    # Check user was not added
    users = db.t.users
    user = users("email = ?", ("newuser@example.com",))
    assert len(user) == 0

def test_add_user_already_exists(temp_db):
    "Test adding user that already exists."
    message = feed_text({"error": "user_exists"})["mess"]
    db, _ = temp_db
    # Add first user
    add_user("existing@example.com", "Jane Doe", "admin", db)
    # Try to add same user again
    result = add_user("existing@example.com", "Another Name", "user", db)
    result_str = to_xml(result)
    assert message in result_str
    # Check only one user exists with that email
    users = db.t.users
    User= users.dataclass()
    user = users("email = ?", ("existing@example.com",))
    assert len(user) == 1
    assert user[0].name == "Jane Doe"  # Original name preserved

def test_delete_user_not_found(temp_db):
    "Deleting a non-existent user returns user_not_found error."
    message = feed_text({"error": "user_not_found"})["mess"]
    db, _ = temp_db
    result = delete_user("noone@example.com", db)
    result_str = to_xml(result)
    assert message in result_str

def test_delete_user_has_planners(temp_db, clean_files):
    "Deleting a user that has planner associations returns error with centers listed."
    message = feed_text({"error": "user_has_planners"})["mess"]
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
    add_center(center_name, "timez", "mok.db", "laba", "mahi.ok.db", db, ffolder)
    email = "planner@example.com"
    add_user(email, "Planner", "user", db)
    planners.insert(user_email=email, center_name=center_name)
    result = delete_user(email, db)
    result_str = to_xml(result)
    assert message.split(":")[0] in result_str
    assert center_name in result_str

def test_delete_user_success(temp_db):
    "Successfully delete a user with no planner associations."
    message = feed_text({"success": "user_deleted"})["mess"]
    db, _ = temp_db
    email = "todelete@example.com"
    add_user(email, "To Delete", "user", db)
    result = delete_user(email, db)
    result_str = to_xml(result)
    assert message in result_str
    # verify removal from users table
    remaining = db.t.users("email = ?", (email,))
    assert len(remaining) == 0

def test_add_center_success(temp_db, clean_files):
    "Test successfully adding a new center."
    db, _ = temp_db
    message = feed_text({'success': 'center_added'})["mess"]
    ffolder = clean_files
    centers = db.t.centers
    Center = centers.dataclass()
    result = add_center("NewCenter", "timez", "new_center.db", "New Location", "mahi.ok.db",
                        db, ffolder)
    result_str = to_xml(result)
    assert message in result_str
    # Verify center was added
    center = centers("center_name = ?", ("NewCenter",))
    assert len(center) == 1
    assert center[0].location == "New Location"
    assert center[0].gong_db_name == "new_center.db"

def test_add_center_missing_fields(temp_db, clean_files):
    "Test adding center with missing required fields."
    message = feed_text({"error": "missing_fields"})["mess"]
    db, _ = temp_db
    ffolder = clean_files
    centers = db.t.centers
    result = add_center("", "timez", "mahi.ok.db", "laba", "tc.db", db, ffolder)
    result_str = to_xml(result)
    assert message in result_str
    # Check that no center was added
    all_centers = centers()
    assert len(all_centers) == 2

def test_add_center_already_exists(temp_db, clean_files):
    "Test adding a center that already exists."
    message = feed_text({"error": "center_exists"})["mess"]
    db, _ = temp_db
    ffolder = clean_files
    centers = db.t.centers
    Center = centers.dataclass()
    # Add first center
    result = add_center("ExistingCenter", "tz", "existing.db", "Existing Location", "mahi.ok.db",
                        db, ffolder)
    # Try to add same center again
    result = add_center("ExistingCenter", "tz", "different.db", "Different Location",
                        "mahi.ok.db", db, ffolder)
    result_str = to_xml(result)
    assert message in result_str
    # Verify original center unchanged
    center = centers("center_name = ?", ("ExistingCenter",))
    assert len(center) == 1
    assert center[0].location == "Existing Location"
    assert center[0].gong_db_name == "existing.db"
    # clean up created gong db file

def test_add_center_invalid_template(temp_db, clean_files):
    "Test adding center with non-existent template."
    message = feed_text({"error": "template_not_found"})["mess"]
    db, _ = temp_db
    ffolder = clean_files
    centers = db.t.centers
    result = add_center("TemplateTestCenter", "Tz", "template_test.db",
                        "Template Test", "nonexistent_template.db", db, ffolder)
    # Should contain error about template
    result_str = to_xml(result)
    assert message in result_str 
    # Verify center was not added
    center = centers("center_name = ?", ("TemplateTestCenter",))
    assert len(center) == 0

def test_add_center_duplicate_gong_db_name(temp_db, clean_files):
    "Test adding center with duplicate gong_db_name."
    message = feed_text({"error": "db_file_exists"})["mess"]
    db, _ = temp_db
    ffolder = clean_files
    centers = db.t.centers
    Center = centers.dataclass()
    # Add first center
    add_center("Center1", "tz", "shared.db", "Location 2", "mahi.ok.db", db, ffolder)
    # Try to add center with same gong_db_name
    result = add_center("Center2", "tz", "shared.db", "Location 2", "mahi.ok.db",
                        db, ffolder)
    result_str = to_xml(result)
    assert message in result_str
    # Verify only first center exists
    center = centers("center_name = ?", ("Center1",))
    assert len(center) == 1

def test_delete_center_not_found(temp_db, clean_files):
    "Deleting a non-existent center returns center_not_found error."
    message = feed_text({"error": "center_not_found"})["mess"]
    db, _ = temp_db
    ffolder = clean_files
    result = delete_center("NonexistentCenter", db, ffolder)
    result_str = to_xml(result)
    assert message in result_str

def test_delete_center_has_planners(temp_db, clean_files):
    "Deleting a center that has planner associations returns error with users listed."
    message = feed_text({"error": "center_has_planners"})["mess"]
    db, _ = temp_db
    ffolder = clean_files
    centers = db.t.centers
    # Create center, user and planner association
    center_name = "CenterWithPlanners"
    add_center(center_name, "tz", "shared2.db", "Location 2", "mahi.ok.db", db, ffolder)
    email = "planner1@example.com"
    add_user(email, "Planner One", "user", db)
    add_planner(email, center_name, db)
    result = delete_center(center_name, db, ffolder)
    result_str = to_xml(result)
    assert message.split(":")[0] in result_str
    assert email in result_str
    # Verify center was not deleted
    center = centers("center_name = ?", (center_name,))
    assert len(center) == 1

def test_delete_center_success(temp_db, clean_files):
    "Successfully delete a center with no planner associations."
    message = feed_text({'success' : 'center_deleted'})["mess"]
    db, _ = temp_db
    db_path = clean_files
    centers = db.t.centers
    # First add a center
    add_center("CenterToDelete", "tz", "delete_center.db", "Delete Location", "mahi.ok.db",
               db, db_path)
    # Verify center was added
    center = centers("center_name = ?", ("CenterToDelete",))
    assert len(center) == 1
    # Delete the center
    result = delete_center("CenterToDelete", db, db_path)
    result_str = to_xml(result)
    assert message in result_str
    # Verify center is removed from database
    remaining = centers("center_name = ?", ("CenterToDelete",))
    assert len(remaining) == 0

def test_delete_center_removes_gong_db(temp_db, clean_files):
    "Verify that delete_center removes the gong database file."
    message = feed_text({'success' : 'center_deleted'})["mess"]
    db, _ = temp_db
    db_path = clean_files
    centers = db.t.centers
    gong_db_name = "remove_me.db"
    # Add a center
    add_center("CenterWithDB", "tz", gong_db_name, "DB Location", "mahi.ok.db", db, db_path)
    # Verify gong database file exists
    db_file_path = os.path.join(db_path, gong_db_name)
    assert os.path.exists(db_file_path), f"Gong DB file not found at {db_file_path}"
    # Delete the center
    result = delete_center("CenterWithDB", db, db_path)
    result_str = to_xml(result)
    assert message in result_str
    # Verify gong database file is deleted
    assert not os.path.exists(db_file_path), f"Gong DB file still exists at {db_file_path}"    

def test_add_planner_success(temp_db, clean_files):
    "Test successfully adding a new planner."
    message = feed_text({"success" : "planner_added"})["mess"]
    db, _ = temp_db
    ffolder = clean_files
    planners = db.t.planners
    # First create a center and user
    add_center("PlannerCenter", "tz", "planner.db", "Center Location", "mahi.ok.db", db, ffolder)
    add_user("planner@example.com", "Test Planner", "user", db)
    # Add planner association
    result = add_planner("planner@example.com", "PlannerCenter", db)
    result_str = to_xml(result)
    assert message in result_str
    # Verify planner was added
    planner = planners("user_email = ? AND center_name = ?", ("planner@example.com", "PlannerCenter"))
    assert len(planner) == 1

def test_add_planner_missing_fields(temp_db, clean_files):
    "Test adding planner with missing required fields."
    message = feed_text({"error": "missing_fields"})["mess"]
    db, _ = temp_db
    # Try to add planner with empty email
    result = add_planner("", "SomeCenter", db)
    result_str = to_xml(result)
    assert message in result_str
    # Try to add planner with empty center
    result = add_planner("planner@example.com", "", db)
    result_str = to_xml(result)
    assert message in result_str

def test_add_planner_user_not_found(temp_db, clean_files):
    "Test adding planner with non-existent user."
    message = feed_text({"error": "user_not_found"})["mess"]
    db, _ = temp_db
    ffolder = clean_files
    # Create a center but no user
    add_center("TestCenter", "tz", "test.db", "Location", "mahi.ok.db", db, ffolder)
    result = add_planner("nonexistent@example.com", "TestCenter", db)
    result_str = to_xml(result)
    assert message in result_str

def test_add_planner_center_not_found(temp_db, clean_files):
    "Test adding planner with non-existent center."
    message = feed_text({"error": "center_not_found"})["mess"]
    db, _ = temp_db
    # Create a user but no center
    add_user("planner@example.com", "Test Planner", "user", db)
    result = add_planner("planner@example.com", "NonexistentCenter", db)
    result_str = to_xml(result)
    assert "not found" in result_str

def test_add_planner_already_exists(temp_db, clean_files):
    "Test adding a planner association that already exists."
    message = feed_text({"error": "planner_exists"})["mess"]
    db, _ = temp_db
    ffolder = clean_files
    planners = db.t.planners
    # Create center and user
    add_center("ExistingCenter", "tz", "existing.db",  "Location", "mahi.ok.db", db, ffolder)
    add_user("existing@example.com", "Existing Planner", "user", db)
    # Add planner first time
    add_planner("existing@example.com", "ExistingCenter", db)
    # Try to add same planner again
    result = add_planner("existing@example.com", "ExistingCenter", db)
    result_str = to_xml(result)
    assert message in result_str
    # Verify only one planner record exists
    planner = planners("user_email = ? AND center_name = ?", ("existing@example.com", "ExistingCenter"))
    assert len(planner) == 1

def test_add_planner_multiple_planners_same_center(temp_db, clean_files):
    "Test adding multiple planners to the same center."
    message = feed_text({"success" : "planner_added"})["mess"]
    db, _ = temp_db
    ffolder = clean_files
    planners = db.t.planners
    # Create center
    add_center("SharedCenter", "tz", "shared3.db", "Shared Location", "mahi.ok.db", db, ffolder)
    # Add multiple users and planners
    for i in range(3):
        email = f"planner{i}@example.com"
        add_user(email, f"Planner {i}", "user", db)
        result = add_planner(email, "SharedCenter", db)
        result_str = to_xml(result)
        assert message in result_str
    # Verify all planners were added
    all_planners = planners("center_name = ?", ("SharedCenter",))
    assert len(all_planners) == 3

def test_add_planner_same_user_multiple_centers(temp_db, clean_files):
    "Test adding the same user as planner to multiple centers."
    message = feed_text({"success" : "planner_added"})["mess"]
    db, _ = temp_db
    ffolder = clean_files
    planners = db.t.planners
    # Create user
    add_user("versatile@example.com", "Versatile Planner", "user", db)
    # Add multiple centers
    for i in range(3):
        add_center(f"Center{i}", "tz", f"center{i}.db", f"Location {i}", "mahi.ok.db", db, ffolder)
        result = add_planner("versatile@example.com", f"Center{i}", db)
        result_str = to_xml(result)
        assert message in result_str
    # Verify all planner associations were added
    user_planners = planners("user_email = ?", ("versatile@example.com",))
    assert len(user_planners) == 3

def test_delete_planner_last_planner(temp_db, clean_files):
    "Deleting the only planner for a center should return last_planner_for_center error."
    message = feed_text({"error": "last_planner_for_center"})["mess"]
    db, _ = temp_db
    ffolder = clean_files
    centers = db.t.centers
    planners = db.t.planners
    # Create center and one planner
    add_center("SoloCenter", "tz", "solo.db", "Location", "mahi.ok.db", db, ffolder)
    add_user("solo_planner@example.com", "Solo Planner", "user", db)
    add_planner("solo_planner@example.com", "SoloCenter", db)
    # Attempt to delete the last planner
    result = delete_planner("solo_planner@example.com", "SoloCenter", db)
    result_str = to_xml(result)
    # message may include additional text after ":" so compare prefix
    assert message.split(":")[0] in result_str
    assert "SoloCenter" in result_str
    # planner should still exist
    remaining = planners("user_email = ? AND center_name = ?", ("solo_planner@example.com", "SoloCenter"))
    assert len(remaining) == 1

def test_delete_planner_success(temp_db, clean_files):
    "Deleting a planner when there are multiple planners for the center should succeed."
    message = feed_text({"success": "planner_deleted"})["mess"]
    db, _ = temp_db
    ffolder = clean_files
    planners = db.t.planners
    # Create center and two planners
    add_center("MultiCenter", "tz", "multi.db", "Location", "mahi.ok.db", db, ffolder)
    add_user("p1@example.com", "Planner One", "user", db)
    add_user("p2@example.com", "Planner Two", "user", db)
    add_planner("p1@example.com", "MultiCenter", db)
    add_planner("p2@example.com", "MultiCenter", db)
    # Delete one planner
    result = delete_planner("p1@example.com", "MultiCenter", db)
    result_str = to_xml(result)
    assert message in result_str
    # Verify the deleted planner record is gone and the other remains
    p1 = planners("user_email = ? AND center_name = ?", ("p1@example.com", "MultiCenter"))
    p2 = planners("user_email = ? AND center_name = ?", ("p2@example.com", "MultiCenter"))
    assert len(p1) == 0
    assert len(p2) == 1
