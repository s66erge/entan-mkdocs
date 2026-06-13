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
            await state_mach.abandon_changes()
        if state_mach.configuration[0].id == "free":
            state_mach.model.user = this_user
            await state_mach.progress()
            center_is_free = True
        return center_is_free

async def abandon_edit(session, csms):
    this_center = session[utils.Skey.CENTER]
    session[utils.Skey.CENTER] = ""
    if this_center in csms and csms[this_center].configuration[0].id == "edit":
        await csms[this_center].abandon_changes()
        csms[this_center].model.user = None
    elif session[utils.Skey.ROLE] == "admin":
        print("Admin is abandoning changes for center ",this_center)
        await csms[this_center].send("force_to_free")
    return  Redirect('/dashboard')

async def timer_done(session, csms):
    this_center = session[utils.Skey.CENTER]
    session[utils.Skey.CENTER] = ""
    await csms[this_center].edit_timer_done()
    csms[this_center].model.user = None    
    return  Redirect('/dashboard')

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center_transitions.md#system-transitions>>[init]

async def save_db_plan_times(sm):
    save_db_file = await planning.save_db_plan_timetable(sm.model.center_name, sm.model.centers)
    sm.model.save_db_filename = save_db_file
    sm.model.center_params = minio.params_from_excel_minio(sm.model.center_name)
    await asyncio.to_thread(minio.remove_center_temp_data, sm.model.center_name)
    return {"success": f"new db saved as {save_db_file}"}

async def get_delay(sm, until_hour, minutes=0):
    center_tz = ZoneInfo(sm.model.center_params[utils.Pkey.TIMEZON])
    now_center = datetime.now(center_tz)
    next_event = now_center.replace(hour=until_hour, minute=minutes)
    if now_center.hour > until_hour or \
        (now_center.hour == until_hour and now_center.minute >= minutes):
        # If it's already past the target time, schedule for tomorrow
        next_event +=  timedelta(days=1)
    if sm.model.center_name == utils.Globals.TEST_CENTER or \
        sm.model.get_user() == utils.Globals.DEV_USER:
        print(sm.model.get_user(), sm.model.center_name, " - using short delay for testing")
        delay = utils.Globals.SHORT_DELAY * 1000
    else:
        delay =  (next_event - now_center).total_seconds() * 1000
    result = {"success": f"Date/time now at center: {datetime.now(center_tz).isoformat()}"}
    return result, delay

async def transfer_new_db(sm):
    try:
        center_tz = ZoneInfo(sm.model.center_params[utils.Pkey.TIMEZON])
        center_date = datetime.now(center_tz).date().strftime("%Y-%m-%d")
        sm.model.center_date = center_date
        file_complete = utils.get_db_path() + sm.model.save_db_filename
        minio_object = f"{sm.model.center_name.lower()}/{utils.Globals.SENDING}{center_date}.db"
        await asyncio.to_thread(minio.file_upload, utils.Globals.PI_BUCKET, minio_object, file_complete)
        print(file_complete, " uploaded to minio as ", minio_object, "in bucket ", utils.Globals.PI_BUCKET)
    except (S3Error, MinioException, RuntimeError) as e:
        result = {"error": f"saving new db to minio failed: {e}"}
    else:
        result = {"success": f"production db -{minio_object}- sent at {datetime.now(center_tz).isoformat()} center time"}
    finally:
        return result

async def delete_new_db(sm):
    try:
        objects_in_minio = minio.get_objects_list(utils.Globals.PI_BUCKET, f"{sm.model.center_name.lower()}")
        if f"{sm.model.center_name.lower()}/{utils.Globals.RECEIVED}{sm.model.center_date}.db" in objects_in_minio:            
            await asyncio.to_thread(minio.delete_object, utils.Globals.PI_BUCKET,
                                    f"{sm.model.center_name.lower()}",f"{utils.Globals.RECEIVED}{sm.model.center_date}.db")
            ok_db_file = utils.get_db_path() + dbset.gong_db_name(sm.model.center_name)
            old_db_file = utils.get_db_path() + dbset.gong_db_name(sm.model.center_name, "old")
            try:
                os.remove(old_db_file)
            except FileNotFoundError:
                pass
            os.rename(ok_db_file, old_db_file)            
            os.rename(utils.get_db_path() + sm.model.save_db_filename, ok_db_file)
            sm.model.centers.update(center_name = sm.model.center_name, pi_db_date = sm.model.center_date)
            result = {"success": f"confirmation of production version {sm.model.center_date} is OK"}
        else:
            result = {"error": f"production file '{utils.Globals.RECEIVED}{sm.model.center_date}.db' NOT PRESENT in minio"}
    except (S3Error, MinioException, RuntimeError) as e:
        result = {"error": f"production version {sm.model.center_date} NOT CONFIRMED as minio deletion failed: {e}"}
    finally:
        return result

# ~/~ end
# ~/~ end
