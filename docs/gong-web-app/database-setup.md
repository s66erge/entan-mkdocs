# Database setup and init

```{.python file=libs/dbset.py}
import textwrap
import os
from fasthtml.common import database
from libs.utils import isa_dev_computer

<<getdb-path>>
<<setup-database>>
<<initialize-database>>
```
### Database path

```{.python #getdb-path}
def get_db_path():
    root = "" if isa_dev_computer() else os.environ.get('RAILWAY_VOLUME_MOUNT_PATH',"None")
    return root + "data/"
```

### Database setup

```{.python #setup-database}

def create_tables(db):
    SQL_CREATE_ROLES = """
    CREATE TABLE IF NOT EXISTS roles (
        role_name TEXT PRIMARY KEY,
        description TEXT
    );
    """
    SQL_CREATE_CENTERS = """
    CREATE TABLE IF NOT EXISTS centers (
        center_name TEXT PRIMARY KEY,
        gong_db_name TEXT,
        location TEXT,
        other_course TEXT
    );
    """
    SQL_CREATE_USERS = """
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        name TEXT,
        role_name TEXT,
        magic_link_token TEXT,
        magic_link_expiry TIMESTAMP,
        is_active BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (role_name) REFERENCES roles(role_name)
    );

    """
    SQL_CREATE_PLANNERS = """
    CREATE TABLE IF NOT EXISTS planners (
        user_email TEXT,
        center_name TEXT,
        PRIMARY KEY (user_email, center_name),
        FOREIGN KEY (user_email) REFERENCES users(email),
        FOREIGN KEY (center_name) REFERENCES centers(center_name)
    );
    """
    db.execute(SQL_CREATE_ROLES)
    db.execute(SQL_CREATE_CENTERS)
    db.execute(SQL_CREATE_USERS)
    db.execute(SQL_CREATE_PLANNERS)
```
### Database initialization

Check if any table(s) is(are) empty and insert default values if needed

```{.python #initialize-database}

def init_data(db):

    roles = db.t.roles
    if not roles():
        roles.insert(role_name="admin", description="administrator")
        roles.insert(role_name="user", description="regular user")

    centers = db.t.centers
    other_course_pajjota = textwrap.dedent("""\
            {
            "TRUST MEETING": "Trust WE"
            }
        """).strip('\n')
    if not centers():
        centers.insert(center_name="Mahi", gong_db_name="mahi.db", location = "1396", other_course = "{ }")
        centers.insert(center_name="Pajjota", gong_db_name="pajjota.db", location = "1370", other_course=other_course_pajjota)

    users = db.t.users
    if not users():
        users.insert(email="spegoff@authentica.eu", name="sp1", role_name="admin", is_active=True, magic_link_token=None, magic_link_expiry=None)
        users.insert(email="spegoff@gmail.com", name="sp2", role_name="user", is_active=True)

    planners = db.t.planners
    if not planners():
        planners.insert(user_email= "spegoff@authentica.eu", center_name= "Mahi")
        planners.insert(user_email= "spegoff@gmail.com", center_name= "Pajjota")
```
