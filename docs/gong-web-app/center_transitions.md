# Center machines transitions

The status of a center data is managed with a state machine. The state is persisted into the center table of the central gongUsers database, using an abstract model and a database persistent model.
Here are the transitions processes used by the state machines

```{.python file=libs/transit.py}
import asyncio
from myFasthtml import *
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from libs.send2pi import file_download, file_upload, session_connect
from libs.utils import Globals, bypass, get_db_path, isa_dev_computer

<<user-transitions>>
<<system-transitions>>
```
### The state machine for each center

see: https://python-statemachine.readthedocs.io/en/latest/index.html

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
    state_mach = csms[center_name]
    center_tz = ZoneInfo(centers[center_name].timezone)
    port = centers[center_name].routing_port
    state_mach.progress()
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
        state_mach.progress()
        reason = "OK_file_transfer"
        print(reason)
    except Exception as e:
        state_mach.problem()
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
            state_mach.progress()
            reason = "OK received prod info"
            print(reason)
        except Exception as e:
            state_mach.problem()
            reason = "production info not received"
            err = e
            #return Redirect(f'/transfer_failed?reason=prod&mess={quote_plus(e)}')
        else:
            if date_check(resu, next_date_iso):
                state_mach.progress()
                reason = "OK db production version"
                print(reason)
                #return Redirect('/transfer_success')
            else:
                #return Redirect('/transfer_failed?reason=wrong_date')
                state_mach.problem()
                reason = "in_production_failed"
                print(reason)
                err = "wrong file date"
                state_mach.problem()
        finally:
            pass
    finally:
        state = state_mach.configuration[0].id
        return state, reason, err

```

