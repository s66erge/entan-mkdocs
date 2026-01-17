# ~/~ begin <<docs/gong-web-app/0-gong-prog.md#main.py>>[init]

import sys
from functools import wraps
from fasthtml.common import *
#  from starlette.testclient import TestClient

from libs import * 
from libs.auth import admin_required

css = Style(':root {--pico-font-size: 95% ; --pico-font-family: Roboto;}')

def before(req, session):
   auth = req.scope['auth'] = session.get('auth', None)
   if not auth: return RedirectResponse('/login', status_code=303)

bware = Beforeware(before, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', '/login','/', '/create_magic_link', r'/verify_magic_link/.*', r'/magic_button/.*'])

app, rt = fast_app(live=True, debug=True, title="Gong Users", favicon="favicon.ico",
                   before=bware, hdrs=(picolink,css),)

db_path = dbset.get_db_path()
db = dbset.get_central_db()

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
def get(request, token: str):
    return auth.verify_link(request, token) 

@rt('/magic_button/{token}')
def get(session, token: str):
    return auth.magic_button(session, token, users) 

# client = TestClient(app)

@rt('/')
def home():
    return Main(
        Div(utils.display_markdown("home-t")),
        A("Login",href="/login", class_="button"),
        cls="container"
    )

@rt('/dashboard')
def get(session):
    return cdash.dashboard(session, db)

@rt('/consult_page')
def get(session, request):
    return consul.consult_page(session, centers)

@rt('/consult/select_db')
def get(request):
    return consul.consult_select_db(request, centers, db_path)

@rt('/consult/select_period')
def get(request):
    return consul.consult_select_period(request, db_path)

@rt('/consult/select_timetable')
def get(request):
    return consul.consult_select_timetable(request, db_path)

@rt('/planning_page')
def get(session, request):
    return planning.planning_page(session, request, db)

@rt('/planning/load_dhamma_db')
def get(session, request):
    return planning.load_dhamma_db(session, request, db)

@rt('/planning/show_dhamma')
def get(session, request):
    return planning.show_dhamma(request, db, db_path)

@rt('/planning/set_free')
def get(session, request):
    return planning.set_free(request, db)

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
def post(session, new_center_name: str = "", new_timezone: str = "", new_gong_db_name: str = "", new_center_location: str = "", db_template: str = ""):
    return adchan.add_center(new_center_name, new_timezone, new_gong_db_name, new_center_location, db_template, db, db_path)

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
    del session['role']
    return Redirect('/login')

@rt('/no_access_right')
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
        Div(H2("This feature is not yet implemented.")),
        cls="container"
    )

@rt('/db_error')
def db_error(session, etext: str):
    return Html(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Head(Title("Database error")),
        Body(Div(utils.feedback_to_user({'error': 'db_error', 'etext': f'{etext}'}))),
        (A("Dashboard", href="/dashboard")),
        cls="container"
    )

serve()
# ~/~ end
