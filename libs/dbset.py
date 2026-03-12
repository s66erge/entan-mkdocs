# ~/~ begin <<docs/gong-web-app/database-setup.md#libs/dbset.py>>[init]
from myFasthtml import *
import textwrap
import os
# import Database # for PostgreSQL, moved to # from myFasthtml 
# import database # for SQLite, moved to # from myFasthtml
from libs.utils import isa_dev_computer

# ~/~ begin <<docs/gong-web-app/database-setup.md#dataclasses>>[init]

class Role: role_name: str; description: str
class User: email: str; name: str; role_name: str; password: str; magic_link_token: str; magic_link_expiry: str; is_active: bool; number_link_touched: int
class Center: center_name: str; timezone: str; gong_db_name: str; location: str; other_course: str; status: str; created_by: str; status_start: str; json_save: str
class Planner: user_email: str; center_name: str

class Coming_periods: start_date: str; period_type: str
class Periods_struct: period_type: str; day: int; day_type: str
class Timetables: period_type: str; day_type: str; time: str; gong_id: int; auto: int; targets: str; comment: str
class Gongs: sound_id: int; repeat: int; interval: float; length: float; comment: str  
class Targets: id: int; shortname: str; longname: str

# ~/~ end
# ~/~ begin <<docs/gong-web-app/database-setup.md#getdb-path>>[init]
def get_db_path():
    if isa_dev_computer():
        root = ""
    elif os.environ.get('Github_CI') == 'true': # Github CI actions
        root = ""
    else:   # Railway production permanent storage
        root = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH',"None") + "/"
    return root + "data/"

# on postgreSQL
def get_central_db():
    if isa_dev_computer():
        # local sqlite3
        return database(get_db_path() + "gongUsers.db")
        # local postgreSQL on docker
        #return Database("postgresql://postgres:route66@localhost:5432/postgres")
    else:
        return Database(os.environ.get('DATABASE_URL'))

    #return Database("postgresql://postgres:route66@db:5432/postgres")

# on SQLite
#def get_central_db():
#    return database(get_db_path() + "gongUsers.db")

# ~/~ end
# ~/~ begin <<docs/gong-web-app/database-setup.md#setup-database>>[init]

def init_data(roles, users, centers, planners):

    if not roles():
        roles.insert(role_name="admin", description="administrator")
        roles.insert(role_name="user", description="regular user")

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
        centers.insert(center_name="Mahi", gong_db_name="mahi.ok.db", location="1396", timezone="Europe/Paris", other_course=oc_mahi,  status="free", created_by="", status_start="2026-01-08T16:35:42+00:00", json_save="")
        centers.insert(center_name="Pajjota", gong_db_name="pajjota.ok.db", location="1370", timezone="Europe/Brussels", other_course=oc_pajj, status="free", created_by="", status_start="2026-01-08T16:35:42+00:00", json_save="")
    else:
        centers.update(center_name="Mahi", other_course=oc_mahi)
        centers.update(center_name="Pajjota", other_course=oc_pajj)

    if not users():
        users.insert(email="spegoff@authentica.eu", name="sp1", role_name="admin", is_active=True, magic_link_token=None, magic_link_expiry=None)
        users.insert(email="spegoff@gmail.com", name="sp2", role_name="user", is_active=True)

    if not planners():
        planners.insert(user_email= "spegoff@authentica.eu", center_name= "Mahi")
        planners.insert(user_email= "spegoff@gmail.com", center_name= "Pajjota")
# ~/~ end
# ~/~ end
