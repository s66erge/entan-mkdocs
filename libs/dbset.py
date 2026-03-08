# ~/~ begin <<docs/gong-web-app/database-setup.md#libs/dbset.py>>[init]
import textwrap
import os
from myFasthtml import database
from libs.utils import isa_dev_computer

# ~/~ begin <<docs/gong-web-app/database-setup.md#getdb-path>>[init]
def get_db_path():
    if isa_dev_computer():
        root = ""
    elif os.environ.get('Github_CI') == 'true': # Github CI actions
        root = ""
    else:   # Railway production permanent storage
        root = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH',"None") + "/"
    return root + "data/"

def get_central_db():
    return database(get_db_path() + "gongUsers.db")
# ~/~ end
# ~/~ begin <<docs/gong-web-app/database-setup.md#setup-database>>[init]

db = get_central_db()
class Role: role_name: str; description: str
roles = db.t.roles if db.t.roles.exists() else db.create(Role, pk='role_name')

class User: email: str; name: str; role_name: str; password: str; magic_link_token: str; magic_link_expiry: str; is_active: bool; number_link_touched: int
users = db.t.users if db.t.users.exists() else db.create(User, pk='email')

class Center: center_name: str; timezone: str; gong_db_name: str; location: str; other_course: str; status: str; current_user: str; status_start: str; json_save: str
centers = db.t.centers if db.t.centers.exists() else db.create(Center, pk='center_name')

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
        timezone TEXT,
        gong_db_name TEXT,
        location TEXT,
        other_course TEXT,
        status TEXT,
        current_user TEXT
    );
    """
    SQL_CREATE_USERS = """
    CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY,
        name TEXT,
        role_name TEXT,
        password TEXT,
        magic_link_token TEXT,
        magic_link_expiry TIMESTAMP,
        is_active BOOLEAN DEFAULT FALSE,
        number_link_touched INT,
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
    #db.execute(SQL_CREATE_ROLES)
    #db.execute(SQL_CREATE_CENTERS)
    #db.execute(SQL_CREATE_USERS)
    db.execute(SQL_CREATE_PLANNERS)
# ~/~ end
# ~/~ begin <<docs/gong-web-app/database-setup.md#initialize-database>>[init]

def init_data(db):

    roles = db.t.roles
    if not roles():
        roles.insert(role_name="admin", description="administrator")
        roles.insert(role_name="user", description="regular user")

    centers = db.t.centers
    oc_mahi = textwrap.dedent("""\
    {
    "replacements": {"Other": {"TRUSTMEETING": "Trust WE"},
                     "ServicePeriod": {"INBETWEEN": "IN BETWEEN"}},
    "delete": {"IN BETWEEN": "@ALL@", "1 day": "Service",
               "Children / teens": "Service"}
    }    
    """).strip('\n')
    oc_pajj = textwrap.dedent("""\
    {
    "replacements": {"Other": {"TRUSTMEETING": "Trust WE"},
                     "ServicePeriod": {"@ALL@": "IN BETWEEN"}},
    "delete": {"IN BETWEEN": "@ALL@"}
    }
    """).strip('\n')
    if not centers():
        centers.insert(center_name="Mahi", gong_db_name="mahi.ok.db", location="1396", timezone="Europe/Paris", other_course=oc_mahi,  status="free", current_user="", status_start="2026-01-01", json_save="")
        centers.insert(center_name="Pajjota", gong_db_name="pajjota.ok.db", location="1370", timezone="Europe/Brussels", other_course=oc_pajj, status="free", current_user="", status_start="2026-01-01", json_save="")
    else:
        centers.update(center_name="Mahi", other_course=oc_mahi)
        centers.update(center_name="Pajjota", other_course=oc_pajj)

    users = db.t.users
    if not users():
        users.insert(email="spegoff@authentica.eu", name="sp1", role_name="admin", is_active=True, magic_link_token=None, magic_link_expiry=None)
        users.insert(email="spegoff@gmail.com", name="sp2", role_name="user", is_active=True)

    planners = db.t.planners
    if not planners():
        planners.insert(user_email= "spegoff@authentica.eu", center_name= "Mahi")
        planners.insert(user_email= "spegoff@gmail.com", center_name= "Pajjota")
# ~/~ end
# ~/~ end
