# Center dashboard page

Will only be reachable for authenticated users.

```python
#| file: libs/cdash.py 

from fasthtml.common import *
from datetime import datetime
from urllib.parse import quote
import libs.utils as utils
import libs.minio as minio
import libs.dbset as dbset
import pandas as pd

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
                Span(style="display: inline-block; width: 100px;"),
                Button("Download PDF", onclick="window.print()"),

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
        Button("SEE THE COMPLETE STATUS AND CONFIGURATION OF THIS CENTER", type="submit", onclick="document.getElementById('myForm').action='/status_page'"),
        Button("MODIFY CENTER PLANNING: ONLY IF YOU ARE A REGISTERED PLANNER FOR THIS CENTER", 
               type="submit", onclick="document.getElementById('myForm').action='/planning_page'"),
        action="/default_route",
        id="myForm",
        method="get",
    )
    return Main(
        top_menu(session['role']),
        Div(P(f"You are logged in as '{u.email}' with role '{u.role_name}'"),
            P(""),
            Div(utils.display_markdown("dashboard-t")),
            P(A("CONSULT THE PLANNING AND TIMETABLES OF ANY CENTER", href="/consult_page",
                style="font-size: 24px;")),
            Div(
                P("Choose a center:"),
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
    state_mach = csms[center_name]
    state = state_mach.configuration[0].id
    email = session[utils.Skey.AUTH]
    user_timezone = users[email].timezone
    center_obj = centers[center_name]
    pi_database_date = center_obj.pi_db_date
    config_file = minio.get_excel_minio(center_name)
    params = minio.params_from_excel_minio(center_name)
    ct_timezone = params[utils.Pkey.TIMEZON]
    db_file = utils.get_db_path() + dbset.gong_db_name(center_name)
    db_center = database(db_file)
    gongs_df = pd.DataFrame(db_center.t.gongs())
    targets_df = pd.DataFrame(db_center.t.targets())
    db_center.close()
    replace_df = pd.DataFrame(minio.dicts_from_excel_minio(center_name,"replacement"))
    inside_df = pd.DataFrame(minio.dicts_from_excel_minio(center_name,"inside"))
    html_gongs = gongs_df.fillna("").to_html(index=False)
    html_targets = targets_df.fillna("").to_html(index=False)
    html_replace = replace_df.fillna("").to_html(index=False)
    html_inside = inside_df.fillna("").to_html(index=False)
    mark_file = "planning-free-t" if state == "free" else "planning-busy-t"
    return Main(
        top_menu(session['role']),
        Div(utils.display_markdown(mark_file)),
        H1(f"{center_name}"),
        P(f"Current center state: {state}", Br(),
          f"Local database in center was installed on: {pi_database_date}"),
        P(f"Center timezone: {ct_timezone}, local center time now: {utils.short_iso(datetime.now() , ct_timezone)}", Br(),
          f"Your browser timezone: {user_timezone}, your time now: {utils.short_iso(datetime.now(), user_timezone)}", Br(),
          f"UTC time now: {utils.short_iso(datetime.now())}"),
        P(f"Last result: {state_mach.model.last_result}") if state_mach.model.last_result else None,
        H3("Center gongs and targets"),
        Safe(html_gongs),
        Safe(html_targets),
        P(f"Default gong id for copied periods: {params[utils.Pkey.GONG_ID]}", Br(),
          f"Default target(s) for copied periods: {params[utils.Pkey.TARGETS]}"),
        H3("Configuration"),
        Div(H4("dhamma.org period types replacement table"),
            Safe(html_replace)) if len(replace_df) > 0 else P("No data in the 'replacement' table"),
        Div(H4("gong planning instructions for dhamma.org periods overlaps/gaps"),
            Safe(html_inside)) if len(inside_df) > 0 else P("No data in the 'overlap/gaps' table"),
        P(f"Parameters: {params}"),
        H3("Center states history"),
        Ul(*[Li(item) for item in csms[center_name].active_listeners[0].entries[::-1]]),
        Div(
            H4("Download the center configuration or database (see the production date above)"),
            A("Download excel configuration", href=f"/download_file?filepath={config_file}",
              hx_no_process="true", hx_boost="false", download="", target="_blank"),
            Br(),
            A("Download DB", href=f"/download_file?filepath={db_file}",
              hx_no_process="true", hx_boost="false", download="", target="_blank"),
            Br(),Br(),
            A("set FREE",href="/planning/abandon_edit") 
        ) if session[utils.Skey.ROLE] == "admin" else None,
        cls="container"
    )

async def download_file(file_path):
    filename = Path(file_path).name
    extension = Path(file_path).suffix 
    utf8_filename = quote(filename)
    headers = {
        "Content-Disposition": f"attachment; filename=\"{filename}\"; filename*=UTF-8''{utf8_filename}",
        # --- ADD THESE CACHE-BUSTING HEADERS ---
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0",
        "X-Content-Type-Options": "nosniff"
    }    
    return FileResponse(
        file_path,
        media_type=utils.Globals.MEDIA_TYPES[extension] ,
        headers=headers
    )

```
