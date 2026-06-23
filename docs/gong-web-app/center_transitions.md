# Center machines transitions

The status of a center data is managed with a state machine. The state is persisted into the center table of the central gongUsers database, using an abstract model and a database persistent model.
Here are the transitions processes used by the state machines

```python
#| file: libs/transit.py 

import os
import asyncio
from fasthtml.common import *
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from minio.error import S3Error, MinioException
import libs.utils as utils
import libs.minio as minio
import libs.states as states
import libs.planning as planning
import libs.dbset as dbset

pending_tasks = {}

<<user-transitions>>
<<system-transitions>>
```
### State machines driven during edit state

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
            await state_mach.abandon_changes()
        if state_mach.configuration[0].id == "free":
            state_mach.model.user = this_user
            await state_mach.progress()
            center_is_free = True
        return center_is_free

async def goto_free(session, event, csms):
    this_center = session[utils.Skey.CENTER]
    session[utils.Skey.CENTER] = ""
    await csms[this_center].send(event)
    return  Redirect('/dashboard')

```

# State machines creation and access

1 state machine per center.
To create them: csms = init_center_state_machines()
To access the sm for one center: sm = csms["Mahi"]

```python
#| id: system-transitions

async def save_db_plan_times(model):
    save_db_file = await planning.save_db_plan_timetable(model.center_name, model.centers)
    model.save_db_filename = save_db_file
    model.center_params = minio.params_from_excel_minio(model.center_name)
    await asyncio.to_thread(minio.remove_center_temp_data, model.center_name)
    return {"success": f"new db saved as {save_db_file}"}

async def get_delay(model, until_hour, minutes=0):
    center_tz = ZoneInfo(model.center_params[utils.Pkey.TIMEZON])
    now_center = datetime.now(center_tz)
    next_event = now_center.replace(hour=until_hour, minute=minutes)
    if now_center.hour > until_hour or \
        (now_center.hour == until_hour and now_center.minute >= minutes):
        # If it's already past the target time, schedule for tomorrow
        next_event +=  timedelta(days=1)
    if model.center_name in utils.Globals.TEST_CENTER or \
        model.center_name in utils.Globals.TEST_USER or \
        model.get_user() == utils.Globals.DEV_USER:
        print(model.get_user(), model.center_name, " - using short delay for testing")
        delay = utils.Globals.SHORT_DELAY * 1000
    else:
        delay =  (next_event - now_center).total_seconds() * 1000
    result = {"success": f"Date/time now at center: {datetime.now(center_tz).isoformat()}"}
    return result, delay

async def transfer_new_db(model):
    try:
        center_tz = ZoneInfo(model.center_params[utils.Pkey.TIMEZON])
        center_date = datetime.now(center_tz).date().strftime("%Y-%m-%d")
        model.center_date = center_date
        file_complete = utils.get_db_path() + model.save_db_filename
        minio_object = f"{model.center_name.lower()}/{utils.Globals.SENDING}{center_date}.db"
        await asyncio.to_thread(minio.file_upload, utils.Globals.PI_BUCKET, minio_object, file_complete)
        print(file_complete, " uploaded to minio as ", minio_object, "in bucket ", utils.Globals.PI_BUCKET)
    except (S3Error, MinioException, RuntimeError) as e:
        result = {"error": f"saving new db to minio failed: {e}"}
    else:
        result = {"success": f"production db -{minio_object}- sent at {datetime.now(center_tz).isoformat()} center time"}
    finally:
        return result

def replace_db_files(model):
    ok_db_file = utils.get_db_path() + dbset.gong_db_name(model.center_name)
    old_db_file = utils.get_db_path() + dbset.gong_db_name(model.center_name, "old")
    try:
        os.remove(old_db_file)
    except FileNotFoundError:
        pass
    os.rename(ok_db_file, old_db_file)            
    os.rename(utils.get_db_path() + model.save_db_filename, ok_db_file)
    model.centers.update(center_name = model.center_name, pi_db_date = model.center_date)
    return

async def delete_new_db(model):
    try:
        objects_in_minio = minio.get_objects_list(utils.Globals.PI_BUCKET, f"{model.center_name.lower()}")
        confirmation = f"{model.center_name.lower()}/{utils.Globals.RECEIVED}{model.center_date}.db" in objects_in_minio
        if confirmation or (model.center_name in utils.Globals.TEST_USER):       
            await asyncio.to_thread(minio.delete_object, utils.Globals.PI_BUCKET,
                                    f"{model.center_name.lower()}",f"{utils.Globals.RECEIVED}{model.center_date}.db")
            replace_db_files(model)
            result = {"success": f"confirmation of production version {model.center_date} is OK"}
        else:
            result = {"error": f"production file '{utils.Globals.RECEIVED}{model.center_date}.db' NOT PRESENT in minio"}
    except (S3Error, MinioException, RuntimeError) as e:
        result = {"error": f"production version {model.center_date} NOT CONFIRMED: {e}"}
    finally:
        return result

```

