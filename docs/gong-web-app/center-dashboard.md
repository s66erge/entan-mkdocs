# Center dashboard page

Will only be reachable for authenticated users.

```python
#| file: libs/cdash.py 

from fasthtml.common import *
from datetime import datetime
import libs.utils as utils
import libs.minio as minio

<<dashboard>>
<<status-page>>
```

### Main dashboard

```python
#| id: dashboard

def top_menu(role):
    return Nav(
            Ul(
                Li(A("Admin", href="/admin_page")) if role == "admin" else None,
                Li(A("Dashboard", href="/dashboard")),
                Li(A("Contact", href="/unfinished")),
                Li(A("About", href="/unfinished")),
            ),
            Button("Logout", hx_post="/logout"),
    )

# @rt('/dashboard')
def dashboard(session, users, planners):
    sessemail = session['auth']
    u = users[sessemail]
    user_planners = planners("user_email = ?", (u.email,))
    user_centers = [(p.center_name) for p in user_planners] 
    select = Select(
        Option("Select a center", value="", selected=True),
        *[Option(name, value=name) for name in user_centers],
        name="center",
        id="planning-db-select",
        required=True
    )
    form = Form(
        select,
        Button("MODIFY", type="submit", onclick="document.getElementById('myForm').action='/planning_page'"),
        Button("STATUS", type="submit", onclick="document.getElementById('myForm').action='/status_page'"),
        action="/default_route",
        id="myForm",
        method="get",
    )
    return Main(
        top_menu(session['role']),
        Div(Div(utils.display_markdown("dashboard-t")),
            P(f"You are logged in as '{u.email}' with role '{u.role_name}'"),
            P(""),
            P(A("CONSULT", href="/consult_page")),
            Div(
                P("Choose one of the centers you can modify:"),
                form
            ) if len(user_centers) >= 1 else None,
            cls="container"
        ),
        cls="container",
    )
```

### Status page

```python
#| id: status-page

#@rt('/status_page')
def status_page(session, center_name, centers, users, csms):
    email = session[utils.Skey.AUTH]
    user_timezone = users[email].timezone
    center_obj = centers[center_name]
    # ct_timezone = center_obj.timezone
    params = minio.params_from_excel_minio(center_name)
    ct_timezone = params[utils.Pkey.TIMEZON]
    state_mach = csms[center_name]
    state = state_mach.configuration[0].id
    mark_file = "planning-free-t" if state == "free" else "planning-busy-t"
    return Main(
        top_menu(session['role']),
        Div(utils.display_markdown(mark_file)),
        H3(f"Center {center_name}"),
        P(f"Center timezone: {ct_timezone}, Local time: {utils.short_iso(datetime.now() , ct_timezone)}"),
        P(f"UTC time: {utils.short_iso(datetime.now())}"),
        P(f"Your browser timezone: {user_timezone}, local time: {utils.short_iso(datetime.now(), user_timezone)}"),
        P(f"Current state: {state}"),
        P(f"Last result: {state_mach.model.last_result}") if state_mach.model.last_result else None,
        H3("Center states history"),
        Ul(*[Li(item) for item in csms[center_name].active_listeners[0].entries[::-1]]),
        A("set FREE",href="/planning/abandon_edit") if utils.dev_comp_or_user(session) else None,
        cls="container"
    )

```
