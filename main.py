# ~/~ begin <<docs/gong-web-app/0-gong-prog.md#main.py>>[init]

from myFasthtml import *
from libs.admin import show_page
from libs.adchan import add_planner, delete_planner, add_center, delete_center, add_user, delete_user
from libs.auth import admin_required, verify_code, create_code, login
from libs.cdash import dashboard
from libs.consul import consult_page, consult_select_db, consult_select_period, consult_select_timetable
from libs.dbset import init_data, get_central_db, get_db_path
from libs.planning import planning_page, load_dhamma_db, check_save_show_plan, delete_line, add_line, abandon_edit
from libs.fetch import fetch_dhamma_courses
from libs.states import create_center_state_machines
from libs.utils import feedback_to_user, display_markdown, Globals

#  from starlette.testclient import TestClient

custom_styles = Style("""
.mw-960 { max-width: 960px; }
.mw-480 { max-width: 480px; }
.mx-auto { margin-left: auto; margin-right: auto; }
""")
css = Style(':root {--pico-font-size: 95% ; --pico-font-family: Roboto;}')
htmxsse = Script(src="https://unpkg.com/htmx-ext-sse@2.2.1/sse.js")

def before(req, session):
   auth = req.scope['auth'] = session.get('auth', None)
   if not auth: return Redirect('/login')

bware = Beforeware(before, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css','/login','/', '/create_magic_link', '/verify_code', '/create_code' ])

app, rt = fast_app(live=False, title="Gong Users", favicon="favicon.ico", before=bware, hdrs=(picolink,css,custom_styles,htmxsse),)

db_path = get_db_path()
db = get_central_db()

class Role: role_name: str; description: str
class User: email: str; name: str; role_name: str; password: str; magic_link_token: str; magic_link_expiry: str; is_active: bool; number_link_touched: int
class Center: center_name: str; timezone: str; gong_db_name: str; location: str; other_course: str; status: str; created_by: str; status_start: str; json_save: str
class Planner: user_email: str; center_name: str

roles = db.create(Role, pk='role_name')
users = db.create(User, pk='email')
centers = db.create(Center, pk='center_name')
planners = db.create(Planner, pk=('user_email', 'center_name'))

init_data(roles, users, centers, planners)


csms, clocks = create_center_state_machines(centers)

"""
@rt('/register')
def get():
    return authpass.register_get()

@rt('/registercheck')
def post(email:str, password:str):
    return authpass.register_post(email, password, users)

@rt('/login')
def get():
    return authpass.login_get()

@rt('/logincheck')
def post(session, email:str, password:str):
    return authpass.logincheck(session, email, password, users)
"""
@rt('/login')
def get():
    return login()

@rt('/create_code')
def post(email: str):
    return create_code(email, users)

@rt('/verify_code')
def post(session, code: str):
    return verify_code(session, code, users) 

# client = TestClient(app)

@rt('/')
def home():
    return Main(
        Div(display_markdown("home-t")),
        A("Login",href="/login", class_="button"),
        cls="container"
    )

@rt('/dashboard')
def get(session):
    return dashboard(session, users, planners)

@rt('/consult_page')
def get(session, request):
    return consult_page(session, centers)

@rt('/consult/select_db')
def get(request):
    return consult_select_db(request, centers, db_path)

@rt('/consult/select_period')
def get(request):
    return consult_select_period(request, db_path)

@rt('/consult/select_timetable')
def get(request):
    return consult_select_timetable(request, db_path)

@rt('/planning_page')
async def get(session, request):
    params = dict(request.query_params)
    center = params.get("selected_name")
    return await planning_page(session, center, centers, csms, clocks)

@rt('/planning/load_dhamma_db')
def get(session):
    return load_dhamma_db(session)

@rt('/planning/check_show_dhamma')
async def get(session, request):
    merged_plan = await fetch_dhamma_courses(centers, session["center"], Globals.MONTHS_TO_FETCH, Globals.DAYS_TO_FETCH)
    return await check_save_show_plan(session, merged_plan, centers, {})

@rt('/planning/delete_line/{idx}')
async def post(session, idx: int):
    return await delete_line(session, centers, idx)

@rt('/planning/add_line')
async def post(session, ptype: str, start: str):
    return await add_line(session, centers, ptype, start)

@rt('/planning/abandon_edit')
def get(session):
    return abandon_edit(session, csms)

@rt('/admin_page')
@admin_required
def get(session, request):
    return show_page(request, users, roles, centers, planners)

@rt('/delete_user/{email}')
@admin_required
def post(session, email: str):
    return delete_user(email, users, planners, centers)

@rt('/add_user')
@admin_required
def post(session, new_user_email: str = "", name: str = "",role_name: str =""):
    return add_user(new_user_email, name ,role_name, users, roles, centers)

@rt('/delete_center/{center_name}')
@admin_required
def post(session, center_name: str):
    return delete_center(center_name, users, centers, planners, db_path)

@rt('/add_center')
@admin_required
def post(session, new_center_name: str = "", new_timezone: str = "", new_gong_db_name: str = "", new_center_location: str = "", db_template: str = ""):
    return add_center(new_center_name, new_timezone, new_gong_db_name, new_center_location, db_template, users, centers, db_path)

@rt('/delete_planner/{user_email}/{center_name}')
@admin_required
def post(session, user_email: str, center_name: str):
    return delete_planner(user_email, center_name, planners)

@rt('/add_planner')
@admin_required
def post(session, new_planner_user_email: str = "", new_planner_center_name: str = ""):
    return add_planner(new_planner_user_email, new_planner_center_name, users, centers, planners)

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
def get(request):
    params = dict(request.query_params)
    goto_dash = params.get("goto_dash", "YES")
    return Div(
        Nav(Li(A("Dashboard", href="/dashboard"))) if goto_dash == "YES" else None,
        Div(H3("This feature is not yet implemented."))
        #cls="container"
    )

@rt('/db_error')
def db_error(session, etext: str):
    return Html(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Head(Title("Database error")),
        Body(Div(feedback_to_user({'error': 'db_error', 'etext': f'{etext}'}))),
        (A("Dashboard", href="/dashboard")),
        cls="container"
    )

serve()
# ~/~ end
