# Center machines transitions

The status of a center data is managed with a state machine. The state is persisted into the center table of the central gongUsers database, using an abstract model and a database persistent model.
Here are the transitions processes used by the state machines

```{.python file=libs/transit.py}
import asyncio
from myFasthtml import *
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import libs.utils as utils
from libs.send2pi import file_download, file_upload, session_connect
from libs.utils import Globals, bypass, get_db_path, isa_dev_computer

pending_tasks = {}
prod_version = {}
run_errors = {}

<<user-transitions>>
<<workflow-supervisor>>
<<system-transitions>>
```
### The workflow supervisor

```{.python #workflow-supervisor}

def register_task(center: str, task: asyncio.Task):
    pending_tasks[center] = task
    print(pending_tasks)

async def check_and_advance(center: str, csms):
    sm = csms[center]
    task = pending_tasks.get(center)
    if not task:
        return
    if not task.done():
        return
    result = task.result()
    del pending_tasks[center]
    print(pending_tasks)
    if result:
        sm.progress()
        return
    else:
        sm.problem()
        return
```

```{.python #user-transitions}

async def check_center_free(state_mach, center_lock, this_user):
    async with center_lock:
        center_is_free = False
        tnow = datetime.now(timezone.utc)
        start_state_time = state_mach.model.get_start_time()
        past = datetime.fromisoformat(start_state_time.replace("Z", "+00:00"))
        delta = (tnow-past).total_seconds()
        if state_mach.configuration[0].id == "edit" and delta > Globals.INITIAL_COUNTDOWN:
            # FIXME modify remaining time when user re-enter from "outside"
            state_mach.abandon_changes()
        if state_mach.configuration[0].id == "free":
            state_mach.model.user = this_user
            state_mach.progress()
            center_is_free = True
        return center_is_free, state_mach.configuration[0].id

def abandon_edit(session, csms):
    this_center = session["center"]
    session["center"] = ""
    if this_center in csms and csms[this_center].configuration[0].id == "edit":
        csms[this_center].abandon_changes()
        csms[this_center].model.user = None
    elif bypass(session):
        csms[this_center].force_to_free()
    return  Redirect('/dashboard')

```

# State machines creation and access

1 state machine per center.
To create them: csms = create_center_state_machines()
To access the sm for one center: sm = csms["Mahi"]

```{.python #system-transitions}

async def check_prod_version(center, csms):
    # FIXME after discussion with Ivan
    if utils.isa_dev_computer() and center == utils.Globals.TEST_CENTER:
        return True
    else:
        return False

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

async def send_check_center_db(session, centers, csms, offset, save_db_path):
    center_name = session['center']
    print(f'offset: {offset}')
    states_mach = csms[center_name]
    center_tz = ZoneInfo(centers[center_name].timezone)
    port = centers[center_name].routing_port

    states_mach.progress()   # to wait_01
    now_center, delay_1_s, next_date_iso = get_event_delay(center_tz, hours=1, minutes=0)
    now_here = datetime.now(timezone.utc) - timedelta(minutes=offset)
    print(f"now time at center {now_center}, here {now_here}. Will upload in {delay_1_s/3600} hours")

    states_mach.progress()   # to transfer
    err = "no error"
    await asyncio.sleep(Globals.SHORT_DELAY)
    localDBfilePath = Path(get_db_path() + "/" + "test22.json")
    upload_test(localDBfilePath, port)

    states_mach.progress()  # to wait_02
    delay_2_s = 70 * 60  # seconds: 1 hour and 10 minutes
    await asyncio.sleep(Globals.SHORT_DELAY)

    states_mach.progress()  # to getting_prod
    remoteDBfilePath = Path("/home/pi/test" + "/" + "test22.json")
    resu = download_test(remoteDBfilePath, port)
    prod_version[center_name] = resu

    states_mach.progress()  # to version_check 
    run_errors[center_name] = err
    return

```

