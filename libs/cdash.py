# ~/~ begin <<docs/gong-web-app/center-dashboard.md#libs/cdash.py>>[init]
from myFasthtml import *
from pathlib import Path
import shutil
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from tzlocal import get_localzone
import asyncio
import json
import os
from libs.utils import display_markdown, feedback_to_user, Globals
from libs.dbset import Coming_period, get_db_path

# ~/~ begin <<docs/gong-web-app/center-dashboard.md#dashboard>>[init]

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
# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-dashboard.md#save-center-db>>[init]

async def save_center_db(session, centers, csms):
    center_name = session['center']
    if not session["planOK"]:
        return Div(feedback_to_user({"error": "plan_not_ok"})) 
    state_mach = csms[center_name]
    state_mach.saving_changes()

    source_db_file = get_db_path() + "/" + center_name.lower() + ".ok.db"
    dest_db_file = get_db_path() + "/" + center_name.lower() + ".sending.db"
    if os.path.exists(dest_db_file):
        os.remove(dest_db_file)
    shutil.copy2(Path(source_db_file), Path(dest_db_file))
    dest_db = database(dest_db_file)
    dest_db.execute("DELETE FROM coming_periods")
    #for t in dest_db.t:
    #    dest_db.execute(f"DELETE FROM {str(t)}")
    coming_periods = dest_db.create(Coming_period, pk='start_date')
    for row in json.loads(centers[center_name].json_save):
        coming_periods.insert(start_date=row["start_date"], period_type=row["period_type"])

    center_tz = ZoneInfo(centers[center_name].timezone)
    now_center = datetime.now(center_tz)
    now_here = datetime.now(get_localzone())
    if now_center.hour >= 1:
        # If it's already past 1 AM, schedule for tomorrow
        next_1am = now_center.replace(hour=1, minute=0, second=0, microsecond=0) + timedelta(days=1)
    else:
        next_1am = now_center.replace(hour=1, minute=0, second=0, microsecond=0)
    delay_s = (next_1am - now_center).total_seconds()
    delay_h = delay_s / 3600  
    print(f"now time at center {now_center}, will upload in {delay_h} hours")
    #await asyncio.sleep(delay_s)
    await asyncio.sleep(1)
    #await upload_db()


    print(f"state: {state_mach.current_state.id}")
    state_mach.file_trans_done()
    state_mach.db_prod_done()
    print(f"state: {state_mach.current_state.id}")
    return  Redirect('/dashboard')

# ~/~ end
# ~/~ end
