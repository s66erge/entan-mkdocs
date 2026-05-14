# ~/~ begin <<docs/gong-web-app/center_transitions.md#libs/transit.py>>[init]

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

# ~/~ begin <<docs/gong-web-app/center_transitions.md#user-transitions>>[init]

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
    elif session[utils.Skey.ROLE] == "admin" :
        csms[this_center].force_to_free()
    return  Redirect('/dashboard')

def timer_done(session, csms):
    this_center = session[utils.Skey.CENTER]
    session[utils.Skey.CENTER] = ""
    csms[this_center].edit_timer_done()
    csms[this_center].model.user = None    
    return  Redirect('/dashboard')

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center_transitions.md#workflow-supervisor>>[init]

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

async def retry_on_error(func, *args, retries=3, delay=60, **kwargs):
    if args[0].center_name == utils.Globals.TEST_CENTER:
        delay0 = utils.Globals.SHORT_DELAY
        retries0 = 1
    else:
        delay0 = delay
        retries0 = retries
    for attempt in range(1, retries0 + 1):
        result = await func(*args, **kwargs)
        # Only retry if the function returns {"error": ...}
        if isinstance(result, dict) and "error" in result:
            if attempt < retries0:
                await asyncio.sleep(delay0)
                continue
            return result  # final failure after max retries
        else:
            return result  # success, stop immediately
# ~/~ end
# ~/~ begin <<docs/gong-web-app/center_transitions.md#system-transitions>>[init]

async def save_db_plan_times(model):
    save_db_file = await planning.save_db_plan_timetable(model.center_name, model.centers)
    model.save_db_filename = save_db_file
    await asyncio.to_thread(minio.remove_center_temp_data, model.center_name)
    return {"success": f"new db saved as {save_db_file}"}

async def wait_until(model, until_hour, minutes=0):
    center_tz = ZoneInfo(model.center_params[utils.Pkey.TIMEZON])
    if model.center_name == utils.Globals.TEST_CENTER:
        delay = utils.Globals.SHORT_DELAY
    else:
        now_center = datetime.now(center_tz)
        next_event = now_center.replace(hour=until_hour, minute=minutes)
        if now_center.hour > until_hour or \
            (now_center.hour == until_hour and now_center.minute >= minutes):
            # If it's already past the target time, schedule for tomorrow
            next_event +=  timedelta(days=1)
        delay = (next_event - now_center).total_seconds()
    await asyncio.sleep(delay)
    return {"success": f"Date/time now at center: {datetime.now(center_tz).isoformat()}"} 

async def transfer_new_db(model):
    return await retry_on_error(transfer_new_db_once, model, retries=3, delay=60)
async def transfer_new_db_once(model):
    try:
        center_tz = ZoneInfo(model.center_params[utils.Pkey.TIMEZON])
        center_date = datetime.now(center_tz).date().strftime("%Y-%m-%d")
        model.center_date = center_date
        file_complete = utils.get_db_path() + model.save_db_filename
        minio_object = f"{model.center_name.lower()}/sending{center_date}.db"
        await asyncio.to_thread(minio.file_upload, utils.Globals.PI_BUCKET, minio_object, file_complete)
    except (S3Error, MinioException, RuntimeError) as e:
        return {"error": f"saving new db to minio failed: {e}"}
    else:
        return {"success": f"production db -{minio_object}- sent at {datetime.now(center_tz).isoformat()} center time"}

async def delete_new_db(model):
    return await retry_on_error(delete_new_db_once, model, retries=3, delay=60)
async def delete_new_db_once(model):
    try:
        objects_in_minio = minio.get_objects_list(utils.Globals.PI_BUCKET, f"{model.center_name.lower()}")
        if f"{model.center_name.lower()}/receiving{model.center_date}.db" in objects_in_minio:
            await asyncio.to_thread(minio.delete_object, utils.Globals.PI_BUCKET,
                                    f"{model.center_name.lower()}",f"receiving{model.center_date}.db")
            ok_db_file = utils.get_db_path() + dbset.gong_db_name(model.center_name)
            old_db = database(ok_db_file)
            old_db.close()
            os.remove(ok_db_file)
            os.rename(utils.get_db_path() + model.save_db_filename, ok_db_file)
            model.centers.update(center_name = model.center_name, pi_db_date = model.center_date)
            return {"success": f"production version {model.center_date} deleted"}
        else:
           return {"error": f"production version {model.center_date} NOT FOUND"}
    except (S3Error, MinioException, RuntimeError) as e:
        return {"error": f"deleting production db from minio failed: {e}"}

# ~/~ end
# ~/~ end
