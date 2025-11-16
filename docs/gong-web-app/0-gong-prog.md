# Gong main program 

### Program start


```{.python file=main.py}

import os
import shutil
from functools import wraps
from fasthtml.common import *
# from starlette.testclient import TestClient

from libs import *
from libs.auth import admin_required

css = Style(':root {--pico-font-size: 95% ; --pico-font-family: Pacifico, cursive;}')

def before(req, session):
   auth = req.scope['auth'] = session.get('auth', None)
   if not auth: return RedirectResponse('/login', status_code=303)

bware = Beforeware(before, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', '/login','/', '/create_magic_link', r'/verify_magic_link/.*'])

app, rt = fast_app(live=True, debug=True, title="Gong Users", favicon="favicon.ico",
                   before=bware, hdrs=(picolink,css),)

db_path = "data/" if utils.isa_dev_computer() else os.environ.get('RAILWAY_VOLUME_MOUNT_PATH',"None") + "data/"
db = database(db_path + 'gongUsers.db')

dbset.create_tables(db)
dbset.init_data(db)

users = db.t.users
roles = db.t.roles
centers = db.t.centers
planners = db.t.planners

Role = roles.dataclass()
Center = centers.dataclass()
Planner = planners.dataclass()
User = users.dataclass()

@rt('/login')
def get():
    return auth.login()

@rt('/create_magic_link')
def post(email: str):
    return auth.create_link(email, users)

@rt('/verify_magic_link/{token}')
def get(session, token: str):
    return auth.verify_link(session, token, users) 

# client = TestClient(app)

@rt('/')
def home():
    return Main(
        Div(utils.display_markdown("home")),
        A("Login",href="/login", class_="button"),
        cls="container"
    )

@rt('/dashboard')
def get(session): 
    sessemail = session['auth']
    u = users[sessemail]
    centers = planners("user_email = ?", (u.email,))
    center_names = ", ".join(c.center_name for c in centers)
    return Main(
        Nav(
            Ul(
                Li(A("Admin", href="/admin_page")) if u.role_name == "admin" else None ,
                Li(A(href="/unfinished")("Contact")),
                Li(A("About", href="#")),
            ), 
            Button("Logout", hx_post="/logout"),
        ),
        Div(H1("Dashboard"), P(f"You are logged in as '{u.email}' with role '{u.role_name}' and access to gong planning for center(s) : {center_names}.")),
        cls="container",
    )

@rt('/admin_page')
@admin_required
def get(session, request):
    return admin.show_page(request, db)

@rt('/delete_user/{email}')
@admin_required
def post(session, email: str):
    return adchan.delete_user(email, db)

@rt('/add_user')
@admin_required
def post(session, new_user_email: str = "", name: str = "",role_name: str =""):
    return adchan.add_user(new_user_email, name ,role_name, db)

@rt('/delete_center/{center_name}')
@admin_required
def post(session, center_name: str):
    return adchan.delete_center(center_name, db, db_path)

@rt('/add_center')
@admin_required
def post(session, new_center_name: str = "", new_center_location: str = "",new_gong_db_name: str = "", db_template: str = ""):
    return adchan.add_center(new_center_name, new_center_location, new_gong_db_name, db_template, db, db_path)

@rt('/delete_planner/{user_email}/{center_name}')
@admin_required
def post(session, user_email: str, center_name: str):
    return adchan.delete_planner(user_email, center_name, db)

@rt('/add_planner')
@admin_required
def post(session, new_planner_user_email: str = "", new_planner_center_name: str = ""):
    return adchan.add_planner(new_planner_user_email, new_planner_center_name, db)

@rt('/logout')
def post(session):
    del session['auth']
    return HttpHeader('HX-Redirect', '/login')

@rt('/no_access')
def get():
    return Main(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Div(H1("Access Denied"),
            P("You do not have permission to access this page.")),
        cls="container"
    )

@rt('/unfinished')
def get():
    return Main(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Div(H1("This feature is not yet implemented.")),
        cls="container"
    )

@rt('/db_error')
def db_error(session, etext: str):
    return Html(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Head(Title("Database error")),
        Body(Div(feedb.feedback_to_user({'error': 'db_error', 'etext': f'{etext}'}))),
        (A("Dashboard", href="/dashboard")),
        cls="container"
    )

serve()
```
