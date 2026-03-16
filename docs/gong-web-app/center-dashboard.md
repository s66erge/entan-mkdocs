# Center dashboard page

Will only be reachable for authenticated users.

```{.python file=libs/cdash.py}
from myFasthtml import *
from pathlib import Path
from urllib.parse import quote_plus
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import asyncio
from libs.dbset import get_db_path
import json
import os
from libs.utils import isa_dev_computer, display_markdown, feedback_to_user, Globals
from libs.send2pi import file_download, file_upload, session_connect


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

def get_event_delay(center_tz, hours, minutes):
    now_center = datetime.now(center_tz)
    next_event = now_center.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    if now_center.hour >= hours and now_center.minute >= minutes:
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

async def send_check_center_db(session, centers, csms, offset, save_db_path):
    center_name = session['center']
    print(f'offset: {offset}')
    if not session["planOK"]:
        return {"error": "plan_not_ok"}
    state_mach = csms[center_name]
    center_tz = ZoneInfo(centers[center_name].timezone)
    # PROD-FIX new field "port" in table 'center'
    port = centers[center_name].routing_port
    #save_db_Path = save_db_plan_timetable(center_name, centers)
    state_mach.saving_changes()
    now_center, delay_1_s, next_date_iso = get_event_delay(center_tz, hours=1, minutes=0)
    now_here = datetime.now(timezone.utc) - timedelta(minutes=offset)
    print(f"now time at center {now_center}, here {now_here}. Will upload in {delay_1_s/3600} hours")
    err = "no error"
    reason = ""
    try:
        if isa_dev_computer():
            await asyncio.sleep(Globals.SHORT_DELAY)
            localDBfilePath = Path(get_db_path() + "/" + "test22.json")
            upload_test(localDBfilePath, port)
        else:
            await asyncio.sleep(delay_1_s)
            #upload_real(port)
        state_mach.file_trans_done()
        reason = "OK_file_transfer"
    except Exception as e:
        state_mach.file_not_trans()
        reason = "file_transfer_failed"
        err = e
    else:
        delay_2_s = 70 * 60  # seconds: 1 hour and 10 minutes
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
            reason = "production access failed"
            err = e
            #return Redirect(f'/transfer_failed?reason=prod&mess={quote_plus(e)}')
        else:
            if date_check(resu, next_date_iso):
                state_mach.db_prod_done()
                reason = "OK_db_prod"
                #return Redirect('/transfer_success')
            else:
                state_mach.db_not_prod()
                #return Redirect('/transfer_failed?reason=wrong_date')
                reason = "in_production_failed"
                err = "wrong file date"
        finally:
            pass
    finally:
        state = state_mach.current_state.id
        return state, reason, err

```
