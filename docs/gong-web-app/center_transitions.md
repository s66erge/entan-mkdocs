# Center machines transitions

The status of a center data is managed with a state machine. The state is persisted into the center table of the central gongUsers database, using an abstract model and a database persistent model.
Here are the transitions processes used by the state machines

```python
#| file: libs/transit.py 

import json
import asyncio
from fasthtml.common import *
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
import libs.utils as utils
import libs.send2pi as send2pi
import libs.states as states

pending_tasks = {}

<<user-transitions>>
<<workflow-supervisor>>
<<system-transitions>>
```
### The workflow supervisor

```python
#| id: workflow-supervisor

def register_task(center: str, task: asyncio.Task):
    pending_tasks[center] = task

async def check_and_advance(center: str, csms):
    sm = csms[center]
    task = pending_tasks.get(center)
    if not task:
        return
    if not task.done():
        return
    result = task.result()
    del pending_tasks[center]
    sm.model.last_result = result
    if "success" in result:
        sm.progress()
        return
    else:
        sm.problem()
        return
```

```python
#| id: user-transitions

async def check_center_free(state_mach, this_user):
    center_lock = states.clocks[state_mach.model.center_name]
    async with center_lock:
        center_is_free = False
        tnow = datetime.now(timezone.utc)
        start_state_time = state_mach.model.get_start_time()
        past = datetime.fromisoformat(start_state_time.replace("Z", "+00:00"))
        delta = (tnow-past).total_seconds()
        if state_mach.configuration[0].id == "edit" and delta > utils.Globals.INITIAL_COUNTDOWN:
            state_mach.abandon_changes()
        if state_mach.configuration[0].id == "free":
            state_mach.model.user = this_user
            state_mach.progress()
            center_is_free = True
        return center_is_free

def abandon_edit(session, csms):
    this_center = session[utils.Skey.CENTER]
    session[utils.Skey.CENTER] = ""
    if this_center in csms and csms[this_center].configuration[0].id == "edit":
        csms[this_center].abandon_changes()
        csms[this_center].model.user = None
    elif utils.dev_comp_or_user(session):
        csms[this_center].force_to_free()
    return  Redirect('/dashboard')

def timer_done(session, csms):
    this_center = session[utils.Skey.CENTER]
    session[utils.Skey.CENTER] = ""
    csms[this_center].edit_timer_done()
    csms[this_center].model.user = None    
    return  Redirect('/dashboard')

```

# State machines creation and access

1 state machine per center.
To create them: csms = init_center_state_machines()
To access the sm for one center: sm = csms["Mahi"]

```python
#| id: system-transitions

async def wait_until(model, until_hour, minutes=0):
    # center_tz = ZoneInfo(model.centers[model.center_name].timezone)
    params = utils.params_from_excel_in_db(model.centers[model.center_name])
    center_tz = ZoneInfo(params[utils.Pkey.TIMEZON])
    if model.center_name == utils.Globals.TEST_CENTER:
        delay = utils.Globals.SHORT_DELAY
    else:
        now_center = datetime.now(center_tz)
        next_event = now_center.replace(hour=until_hour, minute=minutes)
        if now_center.hour >= until_hour and now_center.minute >= minutes:
            # If it's already past the target time, schedule for tomorrow
            next_event +=  timedelta(days=1)
        delay = (next_event - now_center).total_seconds()
    await asyncio.sleep(delay)
    return {"success": f"Date/time now at center: {datetime.now(center_tz).isoformat()}"} 

async def transfer_new_db(model):
    # FIXME try 3 times at 10 min. intervals
    localDBPath = Path(utils.get_db_path())
    params = utils.params_from_excel_in_db(model.centers[model.center_name])
    port = int(params[utils.Pkey.ROUTING])
    try:
        if model.center_name == utils.Globals.TEST_CENTER:
            remoteDBPath = Path(utils.Globals.PI_FOLDER_TEST)
            db_file = utils.Globals.PI_FILE_TEST
        else:
            # FIXME after discussion with Ivan        
            remoteDBPath = Path("/home/pi/prod")
            db_file = model.centers[model.center_name].save_db_file

        ssh_session = await asyncio.to_thread(send2pi.session_connect,int(port))
        localDBFilePath = localDBPath / db_file
        await asyncio.to_thread(send2pi.file_upload, localDBFilePath, remoteDBPath, ssh_session)
    except Exception as e:
        return {"error": f"ssh transfer production db failed: {e}"}
    else:
        params = utils.params_from_excel_in_db(model.centers[model.center_name])
        center_tz = ZoneInfo(params[utils.Pkey.TIMEZON])
        # center_tz = ZoneInfo(model.centers[model.center_name].timezone)
        return {"success": f"production db sent at {datetime.now(center_tz).isoformat()} center time"}

async def get_version_prod(model):
    # FIXME try 3 times at 10 min. intervals
    localDBPath = Path(utils.get_db_path())
    params = utils.params_from_excel_in_db(model.centers[model.center_name])
    port = int(params[utils.Pkey.ROUTING])
    try:
        if model.center_name == utils.Globals.TEST_CENTER:
            folder = utils.Globals.PI_FOLDER_TEST
            file = utils.Globals.PI_FILE_TEST
            remoteDBFilePath = Path(folder + "/" + file)
        else:
            # FIXME after discussion with Ivan        
            remoteDBFilePath = Path("/home/pi/prod")
        ssh_session = await asyncio.to_thread(send2pi.session_connect,int(port))
        await asyncio.to_thread(send2pi.file_download, remoteDBFilePath, localDBPath, ssh_session)
        file_transfered = localDBPath / file
        with open(file_transfered, 'r') as f:
            data = json.load(f)
            print(data)
        model.version_prod = data["date"]
    except Exception as e:
        return {"error": f"ssh get production version failed: {e}"}
    else:
       return {"success": f"production version is {data["date"]}"}

async def check_version_prod(model):
    # FIXME after discussion with Ivan
    params = utils.params_from_excel_in_db(model.centers[model.center_name])
    center_tz = params[utils.Pkey.TIMEZON]  
    # now_at_center = datetime.now(ZoneInfo(model.centers[model.center_name].timezone))
    now_at_center = datetime.now(ZoneInfo(center_tz))
    date_at_center = now_at_center.date().isoformat()
    if  date_at_center == model.version_prod:
        return {"success": f"production version OK at center date: {date_at_center}"}
    else:
        return {"error": f"production version is NOT OK with center date: {date_at_center}"}

```

