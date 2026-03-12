# Center dashboard page

Will only be reachable for authenticated users.

```{.python file=libs/cdash.py}
from myFasthtml import *
from pathlib import Path
import shutil
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
# from tzlocal import get_localzone # from myFasthtml
import asyncio
import json
import os
from libs.utils import display_markdown, feedback_to_user, Globals
from libs.dbset import Coming_periods, get_db_path

<<dashboard>>
<<save-center-db>>
```

### Main dashboard

```{.python #dashboard}

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
        name="selected_name",
        id="planning-db-select",
        required=True
    )
    form = Form(
        select,
        Button("MODIFY", type="submit"),
        action="/planning_page",
        method ="get",
    )
    return Main(
        top_menu(session['role']),
        Div(Div(display_markdown("dashboard-t")),
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
### saving the center db and sending to center pi

```{.python #save-center-db}

async def save_center_db(session, centers, csms):
    center_name = session['center']
    if not session["planOK"]:
        return Div(feedback_to_user({"error": "plan_not_ok"})) 
    state_mach = csms[center_name]

    source_db_file = get_db_path() + "/" + center_name.lower() + ".ok.db"
    dest_db_file = get_db_path() + "/" + center_name.lower() + ".sending.db"
    if os.path.exists(dest_db_file):
        os.remove(dest_db_file)
    shutil.copy2(Path(source_db_file), Path(dest_db_file))
    dest_db = database(dest_db_file)
    dest_db.execute("DROP TABLE coming_periods")
    #for t in dest_db.t:
    #    dest_db.execute(f"DROP TABLE {str(t)}")
    coming_periods = dest_db.create(Coming_periods, pk='start_date')
    for record in json.loads(centers[center_name].json_save):
        coming_periods.insert(start_date=record["start_date"], period_type=record["period_type"])
        #dest_db.execute("""
        #INSERT INTO coming_periods (start_date, period_type) 
        #VALUES (?, ?)
        #""", [record["start_date"], record["period_type"]])

    center_tz = ZoneInfo(centers[center_name].timezone)
    now_center = datetime.now(center_tz)
    now_here = datetime.now(get_localzone())
    if now_center.hour >= 1:
        # If it's already past 1 AM, schedule for tomorrow
        next_1am = now_center.replace(hour=1, minute=0, second=0, microsecond=0) + timedelta(days=1)
    else:
        next_1am = now_center.replace(hour=1, minute=0, second=0, microsecond=0)
    next_2am = next_1am + timedelta(hours=1, minutes=10)

    delay_s = (next_1am - now_center).total_seconds()
    delay_h = delay_s / 3600  
    print(f"now time at center {now_center}, will upload in {delay_h} hours")
    state_mach.saving_changes()
    #await asyncio.sleep(delay_s)
    await asyncio.sleep(1)
    #upload_db()

    state_mach.file_trans_done()
    state_mach.db_prod_done()
    return  Redirect('/dashboard')

```
