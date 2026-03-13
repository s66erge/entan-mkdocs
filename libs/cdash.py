# ~/~ begin <<docs/gong-web-app/center-dashboard.md#libs/cdash.py>>[init]
from myFasthtml import *
from pathlib import Path
from urllib.parse import quote_plus
import shutil
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo
import asyncio
import json
import os
from libs.utils import isa_dev_computer, display_markdown, feedback_to_user, Globals
from libs.dbset import Coming_periods, get_db_path
from libs.send2pi import file_download, file_upload, session_connect


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

def save_db_plan_timetable(center_name, centers):
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
    return Path(dest_db_file)

def get_event_delay(center_tz, hours, minutes, next_day):
    now_center = datetime.now(center_tz)
    next_event = now_center.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    if next_day and now_center.hour >= hours and now_center.minute >= minutes:
        # If it's already past the target time, schedule for tomorrow
        next_event +=  timedelta(days=1)
    next_date_iso = next_event.date().isoformat()
    delay_s = (next_event - now_center).total_seconds()
    return now_center, delay_s, next_date_iso  

def upload_test(localDBfilePath, port):
    remoteDBpath = Path("/home/pi/test")
    ssh_session = session_connect(port)
    file_upload(localDBfilePath, remoteDBpath, ssh_session)

def download_test(remoteDBfilePath, port):
    localDBpath = Path(get_db_path())
    ssh_session = session_connect(port)
    file_download(remoteDBfilePath, localDBpath, ssh_session)

def date_check(resu, next_date_iso):
    # FIXME after discussion with Ivan
    return True

async def save_center_db(session, centers, csms):
    center_name = session['center']
    if not session["planOK"]:
        return Div(feedback_to_user({"error": "plan_not_ok"})) 
    state_mach = csms[center_name]
    center_tz = ZoneInfo(centers[center_name].timezone)
    # PROD-FIX new field in table 'center'
    port = centers[center_name].routing_port
    save_db_Path = save_db_plan_timetable(center_name, centers)
    now_center, delay_1_s, next_date_iso = get_event_delay(center_tz, hours=1, minutes=0, next_day=True)
    print(f"now time at center {now_center}, will upload in {delay_1_s/3600} hours")
    state_mach.saving_changes()
    try:
        if isa_dev_computer():
            await asyncio.sleep(Globals.SHORT_DELAY)
            localDBfilePath = Path(get_db_path() + "/" + "test22.json")
            upload_test(localDBfilePath, port)
        else:
            await asyncio.sleep(delay_1_s)
            #upload_real(port)
        state_mach.file_trans_done()
    except Exception as e:
        state_mach.file_not_trans()
        #return Redirect(f'/transfer_failed?reason=trans&mess={quote_plus(e)}')
        return Redirect('/unfinished')
    else:
        now_center, delay_2_s, next_date_iso = get_event_delay(center_tz, hours=2, minutes=10, next_day=False)
        print(f"now time at center {now_center}, will upload in {delay_1_s/3600} hours")

        try:
            if isa_dev_computer():
                await asyncio.sleep(Globals.SHORT_DELAY)
                remoteDBfilePath = Path("/home/pi/test" + "/" + "test22.json")
                resu = download_test(remoteDBfilePath, port)
            else:
                await asyncio.sleep(delay_2_s)
                #resu = download_real(port)
        except Exception as e:
            state_mach.db_not_prod()
            #return Redirect(f'/transfer_failed?reason=prod&mess={quote_plus(e)}')
            return Redirect('/unfinished')
        else:
            if not date_check(resu, next_date_iso):
                state_mach.db_not_prod()
                #return Redirect('/transfer_failed?reason=wrong_date')
                return Redirect('/unfinished')
            else:
                state_mach.db_prod_done()
                return Redirect('/unfinished')
                #return Redirect('/transfer_success')

# ~/~ end
# ~/~ end
