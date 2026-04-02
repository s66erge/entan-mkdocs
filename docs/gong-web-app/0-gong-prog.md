# Gong main program 

### Program start


```python
#| file: main.py

from fasthtml.common import *  # (1)
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
import libs.minio as minio

#  from starlette.testclient import TestClient

<<initialize-program>>
<<login-authenticate>>
<<consult-centers-plans>>
<<start-save-plan-times>>
<<courses-planning>>
<<timetables-changes>>
<<users-admin>>
<<other-routes>>

```

1. Another annotation MERMAID2  - Found superfences config: 'custom_fences': 'name': 'mermaid', 'class': 'mermaid', 'format': function fence_mermaid at 0x000002B15DA79D00

### Initializations

```python
#| id: initialize-program

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
minio.minio_client = minio.create_minio_client()

roles = db.create(dbset.Role, pk='role_name')
users = db.create(dbset.User, pk='email')
centers = db.create(dbset.Center, pk='center_name')
planners = db.create(dbset.Planner, pk=('user_email', 'center_name'))

dbset.init_data(roles, users, centers, planners)
states.init_center_state_machines(centers)

async def workflow_supervisor():
    while True:
        await asyncio.sleep(5)
        for center in states.csms:
            await transit.check_and_advance(center, states.csms)
@app.on_event("startup")
async def start_supervisor():
    asyncio.create_task(workflow_supervisor())

```
### Routes for authentication

```python
#| id: login-authenticate

@rt('/login')
def get():
    return auth.login()

@rt('/create_code')
def post(email: str):
    return auth.create_code(email, users)

@rt('/verify_code')
def post(session, request, code: str):
    timezon = dict(request.query_params).get('timezone', 'UTC')
    return auth.verify_code(session, code, timezon, users) 

@rt('/')
def home():
    return Main(
        Div(utils.display_markdown("home-t")),
        A("Login",href="/login", class_="button"),
        cls="container"
    )

@rt('/logout')
def post(session):
    del session[utils.Skey.AUTH]
    del session[utils.Skey.ROLE]
    return Redirect('/login')

@rt('/dashboard')
def get(session):
    return cdash.dashboard(session, users, planners)
```

### Routes for consulting plannings/timetables

```python
#| id: consult-centers-plans

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

```

### Routes to start/save planning and timetables

```python
#| id: start-save-plan-times

@rt('/planning_page')
async def get(session, center: str):
    session[utils.Skey.CENTER] = center
    enter_edit_OK = await transit.check_center_free(states.csms[center], session['auth'])
    if enter_edit_OK:
        return await planning.planning_page(session, center, centers, states.csms)
    else:
        return Redirect(f"/status_page?center={center}")

@rt('/status_page')
def get(session, center: str):
    return cdash.status_page(session, center, centers, users, states.csms)

@rt('/planning/abandon_edit')
def get(session):
    minio.remove_center_temp_data(session[utils.Skey.CENTER])
    return transit.abandon_edit(session, states.csms)

@rt('/planning/timer_done')
def get(session):
    minio.remove_center_temp_data(session[utils.Skey.CENTER])
    return transit.timer_done(session, states.csms)

@rt('/save-center-db')
async def get(session):
    if not session[utils.Skey.PLANOK]:
        return utils.feedback_to_user({"error": "plan_not_ok"})
    state_mach = states.csms[session[utils.Skey.CENTER]]
    state_mach.progress()   # from 'edit' to 'save_db'
    return Redirect(f"/status_page?center={session[utils.Skey.CENTER]}")

```

### Routes for planning modification

```python
#| id: courses-planning

@rt('/planning/load_dhamma_db')
def get(session):
    return planning.load_dhamma_db(session)

@rt('/planning/check_show_dhamma')
async def get(session, request):
    merged_plan = await fetch.fetch_dhamma_courses(centers, session[utils.Skey.CENTER],
                        utils.Globals.MONTHS_TO_FETCH, utils.Globals.DAYS_TO_FETCH)
    return await planning.check_save_show_plan(session, merged_plan, centers, {})

@rt('/planning/saved_plan')
async def get(session):
    plan = minio.get_center_temp_data(session[utils.Skey.CENTER], "planning")
    return await planning.check_save_show_plan(session, plan, centers, {"success": "show_plan"})

@rt('/planning/delete_line/{idx}')
async def post(session, idx: int):
    return await planning.delete_line(session, centers, idx)

@rt('/planning/add_line')
async def post(session, ptype: str, start: str):
    return await planning.add_line(session, centers, ptype, start)

```

### Routes for timetables changes

```python
#| id: timetables-changes



```

### Routes for admin

```python
#| id: users-admin

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
def post(session, new_center_name: str = "", center_template: str = ""):
    return adchan.add_center(new_center_name, center_template, users, centers, db_path)

@rt('/upload_config')
async def post(file: UploadFile, center_name: str):
    return await admin.upload_config(file, center_name)

@rt('/download_config/{center_name}')
def get(session, request):
    return admin.download_config(session, request)

@rt("/download_it")
def get(session):
    center = session[utils.Skey.CENTER]
    filename = center + ".xlsx"
    file_path = utils.get_db_path() + filename
    return FileResponse(
        file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )

@rt('/delete_planner/{user_email}/{center_name}')
@admin_required
def post(session, user_email: str, center_name: str):
    return adchan.delete_planner(user_email, center_name, planners)

@rt('/add_planner')
@admin_required
def post(session, new_planner_user_email: str = "", new_planner_center_name: str = ""):
    return adchan.add_planner(new_planner_user_email, new_planner_center_name, users, centers, planners)

```

### Other routes

```python
#| id: other-routes
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
```
