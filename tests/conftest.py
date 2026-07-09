import pytest
from fastlite import database

import libs.dbset as dbset


@pytest.fixture
def tables():
    """In-memory database with the current schema, seeded via dbset.init_data.

    Yields the four table objects the app passes around (roles, users, centers,
    planners) plus the db handle. Seeded contents: roles admin/user; users
    spegoff@authentica.eu and spegoff@gmail.com (both admin); centers Mahi,
    Pajjota, Testx; 5 planner associations.
    """
    db = database(":memory:")
    roles = db.create(dbset.Role, pk="role_name")
    users = db.create(dbset.User, pk="email")
    centers = db.create(dbset.Center, pk="center_name")
    planners = db.create(dbset.Planner, pk=("user_email", "center_name"))
    dbset.init_data(roles, users, centers, planners)
    yield db, roles, users, centers, planners
    db.close()


def add_center_row(centers, name, status="free", created_by=""):
    """Insert a center using the current schema (no location/gong_db_name columns)."""
    centers.insert(
        center_name=name,
        status=status,
        created_by=created_by,
        status_start="2026-01-01T00:00:00+00:00",
    )


def add_user_row(users, email, name, role_name="user", is_active=False):
    users.insert(
        email=email,
        name=name,
        role_name=role_name,
        is_active=is_active,
        magic_link_token=None,
        magic_link_expiry=None,
    )
