# ~/~ begin <<docs/gong-web-app/center_transitions.md#libs/transit.py>>[init]

import json
import asyncio
from fasthtml.common import *
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from minio.error import S3Error, MinioException
import libs.utils as utils
import libs.minio as minio
import libs.states as states
import libs.planning as planning

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
    elif utils.dev_comp_or_user(session):
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
        if now_center.hour >= until_hour and now_center.minute >= minutes:
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
        file_complete = utils.get_db_path() + model.save_db_filename
        minio_object = f"{model.center_name.lower()}/sending{center_date}.db"
        await asyncio.to_thread(minio.file_upload, utils.Globals.PI_BUCKET, minio_object, file_complete)
    except (S3Error, MinioException, RuntimeError) as e:
        return {"error": f"saving new db to minio failed: {e}"}
    else:
        return {"success": f"production db -{minio_object}- sent at {datetime.now(center_tz).isoformat()} center time"}

async def get_version_prod(model):
    return await retry_on_error(get_version_prod_once, model, retries=3, delay=60)
async def get_version_prod_once(model):
    try:
        minio_object = f"{model.center_name.lower()}/{utils.Globals.PI_FILE_JSON}"
        file_downloaded =  utils.get_db_path() + utils.Globals.PI_FILE_JSON
        await asyncio.to_thread(minio.file_download, utils.Globals.PI_BUCKET, minio_object, file_downloaded)
        with open(file_downloaded, 'r') as f:
            data = json.load(f)
        model.version_prod = data[utils.Globals.PI_FILE_KEY1][utils.Globals.PI_FILE_KEY2]
    except (S3Error, MinioException, RuntimeError) as e:
        return {"error": f"getting json from minio failed: {e}"}
    else:
       return {"success": f"production version is {data['general']['db_version']}"}

async def check_version_prod(model):
    params = minio.params_from_excel_minio(model.center_name)
    center_tz = params[utils.Pkey.TIMEZON]  
    now_at_center = datetime.now(ZoneInfo(center_tz))
    date_at_center = now_at_center.date().isoformat()
    if  date_at_center == model.version_prod:
        return {"success": f"production version OK at center date: {date_at_center}"}
    else:
        return {"error": f"production version is NOT OK with center date: {date_at_center}"}

# ~/~ end
# ~/~ end
