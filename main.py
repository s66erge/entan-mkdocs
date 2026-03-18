# ~/~ begin <<docs/gong-web-app/0-gong-prog.md#main.py>>[init]

from myFasthtml import *
import asyncio
import libs.states as states
import libs.auth as auth
from libs.auth import admin_required
import libs.cdash as cdash
import libs.consul as consul
import libs.dbset as dbset
import libs.planning as planning
import libs.fetch as fetch
import libs.admin as admin
import libs.adchan as adchan
import libs.utils as utils
import libs.states as states
import libs.transit as transit

#  from starlette.testclient import TestClient

# ~/~ begin <<docs/gong-web-app/0-gong-prog.md#initialize-program>>[init]
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
# client = TestClient(app)

db_path = utils.get_db_path()
db = dbset.get_central_db()

roles = db.create(dbset.Role, pk='role_name')
users = db.create(dbset.User, pk='email')
centers = db.create(dbset.Center, pk='center_name')
planners = db.create(dbset.Planner, pk=('user_email', 'center_name'))

dbset.init_data(roles, users, centers, planners)
clocks = states.create_center_state_machines(centers)

async def workflow_supervisor():
    while True:
        await asyncio.sleep(5)
        for center in states.csms:
            await transit.check_and_advance(center, states.csms)
@app.on_event("startup")
async def start_supervisor():
    asyncio.create_task(workflow_supervisor())

# ~/~ end
# ~/~ begin <<docs/gong-web-app/0-gong-prog.md#login-authenticate>>[init]

@rt('/login')
def get():
    return auth.login()

@rt('/create_code')
def post(email: str):
    return auth.create_code(email, users)

@rt('/verify_code')
def post(session, code: str):
    return auth.verify_code(session, code, users) 

@rt('/')
def home():
    return Main(
        Div(utils.display_markdown("home-t")),
        A("Login",href="/login", class_="button"),
        cls="container"
    )

@rt('/logout')
def post(session):
    del session['auth']
    del session['role']
    return Redirect('/login')

@rt('/dashboard')
def get(session):
    return cdash.dashboard(session, users, planners)
# ~/~ end
# ~/~ begin <<docs/gong-web-app/0-gong-prog.md#consult-centers-plans>>[init]

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

# ~/~ end
# ~/~ begin <<docs/gong-web-app/0-gong-prog.md#courses-planning>>[init]

@rt('/planning_page')
async def get(session, selected_name: str):
    center = selected_name
    session["center"] = center
    enter_edit_OK, state = await transit.check_center_free(states.csms[center], clocks[center], session['auth'])
    if enter_edit_OK:
        utils.create_temp_path(center)
        return await planning.planning_page(session, center, centers, states.csms, clocks)
    else:
        return Redirect(f"/status_page?center={center}&reason=not_free&state={state}&err=no_error")

@rt('/status_page')
def get(session, center: str):
    return planning.status_page(session, center, centers, states.csms)

@rt('/planning/load_dhamma_db')
def get(session):
    return planning.load_dhamma_db(session)

@rt('/planning/check_show_dhamma')
async def get(session, request):
    merged_plan = await fetch.fetch_dhamma_courses(centers, session["center"],
                        utils.Globals.MONTHS_TO_FETCH, utils.Globals.DAYS_TO_FETCH)
    return await planning.check_save_show_plan(session, merged_plan, centers, {})

@rt('/planning/delete_line/{idx}')
async def post(session, idx: int):
    return await planning.delete_line(session, centers, idx)

@rt('/planning/add_line')
async def post(session, ptype: str, start: str):
    return await planning.add_line(session, centers, ptype, start)

@rt('/planning/abandon_edit')
def get(session):
    utils.delete_temp_path(session["center"])
    return transit.abandon_edit(session, states.csms)

@rt('/save-center-db')
# FIXME move getting user offset to dashboard ?
async def get(session, offset: int):
    users.update(email=session["auth"], offset=offset)
    if not session["planOK"]:
        return utils.feedback_to_user({"error": "plan_not_ok"})
    save_db_path = planning.save_db_plan_timetable(session["center"], centers)
    utils.delete_temp_path(session["center"])
    await transit.send_check_center_db(session, centers, states.csms, offset, save_db_path)
    return Redirect(f"/status_page?center={session["center"]}")


# ~/~ end
# ~/~ begin <<docs/gong-web-app/0-gong-prog.md#users-admin>>[init]

@rt('/admin_page')
@admin_required
def get(session, request):
    return admin.show_page(request, users, roles, centers, planners)

@rt('/delete_user/{email}')
@admin_required
def post(session, email: str):
    return adchan.delete_user(email, users, planners, centers)

@rt('/add_user')
@admin_required
def post(session, new_user_email: str = "", name: str = "",role_name: str =""):
    return adchan.add_user(new_user_email, name ,role_name, users, roles, centers)

@rt('/delete_center/{center_name}')
@admin_required
def post(session, center_name: str):
    return adchan.delete_center(center_name, users, centers, planners, db_path)

@rt('/add_center')
@admin_required
def post(session, new_center_name: str = "", new_timezone: str = "", new_gong_db_name: str = "", new_center_location: str = "", db_template: str = ""):
    return adchan.add_center(new_center_name, new_timezone, new_gong_db_name, new_center_location, db_template, users, centers, db_path)

@rt('/delete_planner/{user_email}/{center_name}')
@admin_required
def post(session, user_email: str, center_name: str):
    return adchan.delete_planner(user_email, center_name, planners)

@rt('/add_planner')
@admin_required
def post(session, new_planner_user_email: str = "", new_planner_center_name: str = ""):
    return adchan.add_planner(new_planner_user_email, new_planner_center_name, users, centers, planners)

# ~/~ end
# ~/~ begin <<docs/gong-web-app/0-gong-prog.md#other-routes>>[init]

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
        Body(Div(utils.feedback_to_user({'error': 'db_error', 'etext': f'{etext}'}))),
        (A("Dashboard", href="/dashboard")),
        cls="container"
    )

serve()
# ~/~ end

# ~/~ end
