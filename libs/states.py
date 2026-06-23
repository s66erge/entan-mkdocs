# ~/~ begin <<docs/gong-web-app/center_machines.md#libs/states.py>>[init]

from abc import ABC
from abc import abstractmethod
import asyncio
from fasthtml.common import *
from datetime import datetime, timezone
from statemachine import State, Event, StateChart
from statemachine.orderedset import OrderedSet
import libs.dbset as dbset
import libs.transit as transit
import libs.utils as utils
import libs.messages as messages

csms = {}
clocks = {}

# ~/~ begin <<docs/gong-web-app/center_machines.md#state-machine>>[init]

class HistoryListener:
    def __init__(self, model):
        self.max_size = 30
        self.model = model
        self.entries = []

    def after_transition(self, event, source, target):
        model = self.model
        result_mess = f" with: {model.last_result}" if model.last_result else ""
        log = f"At {model.get_start_time()}, {model.get_user()} moved {model.center_name} " + \
            f"from {source.id} to {target.id} on {event}" + result_mess
        # to {target.id} or {self.model.get_status_stri()}
        self.entries.append(log)
        print(log)
        if len(self.entries) > self.max_size:
            self.entries.pop(0)

class CenterState(StateChart["CenterDataModel"]):

    test_delay = 3 * 1000
    allow_event_without_transition = False
    atomic_configuration_update = True

    free = State("Planning free to be edited", initial=True)
    edit = State("Planning is being edited")

    class send_to_center(State.Compound):

        save_db = State("Saving new planning in database", initial=True)
        wait_01 = State("Waiting for 1am at center timezone")
        transfer = State("Transferring planning to center") 
        wait_02 = State("Waiting for 2am at center timezone")
        getting_prod = State("Getting production confirmation after center restart")

        progress = save_db.to(wait_01) | wait_01.to(transfer) | transfer.to(wait_02) \
            | wait_02.to(getting_prod)


    w_reco_trans = State("Planning send failed: waiting for file transfer recovery")
    w_reco_prod = State("Confirmation of version failed: waiting for production recovery")
    errorex = State("Error in callback execution")

    progress = free.to(edit) | edit.to(send_to_center) | send_to_center.getting_prod.to(free)
    problem  = send_to_center.transfer.to(w_reco_trans) | send_to_center.getting_prod.to(w_reco_prod)

    abandon_changes   = Event(edit.to(free), name='user abandon changes')
    edit_timer_done   = Event(edit.to(free), name='1 hour edit timer elapsed')
    reco_trans_done   = Event(w_reco_trans.to(send_to_center.wait_01), name='recovery of file transfer done')
    reco_prod_done    = Event(w_reco_prod.to(free), name='recovery of db in production done')

    # used only in dev mode: force to free transitions
    force_to_free = free.from_.any()

    error_execution = send_to_center.to(errorex, on="printerror")

    # ACTIONS ---------------------------------

    def printerror(self, error):
        #error = erro if erro else "NO ERROR TEXT AVAILABLE"
        self.model.last_result = {"error": f"execution error: {error}"}

    async def go_next(self, result, delai=1, sendid = None):
        self.model.last_result = result
        if "success" in result:
            await self.send("progress", delay=delai, send_id=sendid)
            return
        else:
            await self.send("problem")
            return

    async def on_enter_free(self, source):
        print(source)
        self.model.last_result = {"success": "center is free again"}
        if not self.model.testing:
            self.model.clear_user()

    async def on_exit_edit(self):
        self.model.last_result = None

    # async def on_enter_save_db(self):
    #     if not self.model.testing:
    #         result = await transit.save_db_plan_times(self)
    #     else:
    #         result = {"success": "testing: on_enter_save_db"}
    #     return await self.go_next(result)

    async def on_enter_wait_01(self):
        if not self.model.testing:
            result, delay = await transit.get_delay(self, utils.Globals.WAIT01_HOUR , utils.Globals.WAIT01_MINS)
        else:
            delay = self.test_delay
            result = {"success": f"testing: on_enter_wait_01 with delay: {self.test_delay}"}
        self.model.send_id = f"{self.model.center_name}_wait01"
        return await self.go_next(result, delay, self.model.send_id)

    async def on_exit_wait_01(self):
        if self.model.send_id:
            print("Canceling delayed event ", self.model.send_id)
            self.cancel_event(self.model.send_id)

    async def on_enter_transfer(self):
        if not self.model.testing:
            result = await transit.transfer_new_db(self)
        else:
            result = {"success": "testing: on_enter_transfer"}
            print("'Enter' for 'success', anything for 'error'")
            if input("?"):
                result = {"error": f"{result["success"]}"}
        return await self.go_next(result)

    async def on_enter_wait_02(self):
        if not self.model.testing:
            result, delay = await transit.get_delay(self, utils.Globals.WAIT02_HOUR , utils.Globals.WAIT02_MINS)
        else:
            delay = self.test_delay
            result = {"success": f"testing: on_enter_wait_02 with delay: {self.test_delay}"}
        self.model.send_id = f"{self.model.center_name}_wait02"        
        return await self.go_next(result, delay, self.model.send_id)

    async def on_exit_wait_02(self):
        if self.model.send_id:
            print("Canceling delayed event ", self.model.send_id)
            self.cancel_event(self.model.send_id)

    async def on_enter_getting_prod(self):
        if not self.model.testing:
            result = await transit.delete_new_db(self)
        else:
            result = {"success": "testing: on_enter_getting_prod"}
            print("'Enter' for 'success', anything for 'error'")
            if input("?"):
                result = {"error": f"{result["success"]}"}
        return await self.go_next(result)

    async def on_enter_w_reco_prod(self):
        if not self.model.testing:
            admin_emails = self.model.get_admin_planners()
            etext = messages.email_text("w_reco_prod", {"center": self.model.center_name,
                                                        "date": self.model.center_date})
            await asyncio.to_thread(utils.send_email, "Gong center planning NOT confirmed",
                                etext, admin_emails)
        else:
            print("testing: sent email for on_enter_w_reco_prod then return nothing")
        return

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center_machines.md#abstract-with-persistency>>[init]
class AbstractPersistentModel(ABC):
    def __init__(self):
        self._state = None
    def __repr__(self):
        return f"{type(self).__name__}(state={self.state})"
    @property
    def state(self):
        if self._state is None:
            self._state = self._read_state()
        return self._state
    @state.setter
    def state(self, value):
        self._state = value
        self._write_state(value)
    @abstractmethod
    def _read_state(self): ...
    @abstractmethod
    def _write_state(self, value): ...
# ~/~ end
# ~/~ begin <<docs/gong-web-app/center_machines.md#db-persistent-model>>[init]
def status_to_stri(status):
    if status is None:
        return None
    elif isinstance(status, OrderedSet):
        return ",".join(str(v) for v in status)
    else:
        return str(status)

def stri_to_status(strin):
    if strin is None:
        return None
    parts = strin.split(",")
    return parts[0] if len(parts) == 1 else OrderedSet(parts)

class CenterDataModel(AbstractPersistentModel):
    def __init__(self, center_name, centers, planners, users, testing=False, user=None):
        super().__init__()
        self.center_name = center_name
        self.centers = centers
        self.planners = planners
        self.users = users
        self.testing = testing
        self.user = user
        self.sm = None
        self.statustart = None    # Cache for the timestamp of the last state change
        self.last_result = None   # result of the last operation on this machine
        self.center_params = None # cache for center parameters from db/excel, to avoid multiple calls
        self.save_db_filename = None  # new production db filenameto to be sent : 'sending...'
        self.center_date = None  # production version date
        self.send_id = None # id of the delayed send for waiting states, to be able to cancel it if needed

    def _read_state(self):
        row = self.centers[self.center_name]
        self.statustart = row.status_start
        self.user = row.created_by
        return stri_to_status(row.status)

    def _write_state(self, value):
        # Write BOTH state AND current timestamp
        now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        self.statustart = now_utc
        value_stri = status_to_stri(value)
        self.centers.update(
            center_name = self.center_name, 
            status = value_stri,
            status_start = now_utc,
            created_by = self.user
        )

    def get_status_stri(self):
        return status_to_stri(self._read_state())

    def get_start_time(self):
        if self.statustart is None:
            # If statustart is not cached, read it from the database
            row = self.centers[self.center_name]
            self.statustart = row.status_start if row.status_start else None
        return self.statustart

    def get_user(self):
        if self.user is None:
            row = self.centers[self.center_name]
            self.user = row.created_by
        return self.user

    def clear_user(self):
        #self.user = None
        self.centers.update(
            center_name = self.center_name, 
            created_by = None
        )

    def get_admin_planners(self):
        center_planners = self.planners("center_name = ?", (self.center_name,))
        return [p.user_email for p in center_planners if self.users[p.user_email].role_name == "admin"]

    # ACTIONS --------------------------

    def add_machine(self, machine):
        self.sm = machine

    async def go_next(self, result, delai=1, sendid = None):
        self.last_result = result
        if "success" in result:
            await self.sm.send("progress", delay=delai, send_id=sendid)
            return
        else:
            await self.sm.send("problem")
            return

    async def on_enter_save_db(self):
        if not self.testing:
            result = await transit.save_db_plan_times(self)
        else:
            result = {"success": "testing: on_enter_save_db"}
        return await self.go_next(result)

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center_machines.md#create-centers-sms>>[init]

def delete_state_machine(center_name):
    del csms[center_name]
    del clocks[center_name]

def add_center_state_machine(name, centers, planners, users):
    center_state = CenterDataModel(center_name=name, centers=centers, planners=planners, users=users)
    sm = CenterState(model=center_state)
    center_state.add_machine(sm)
    the_listener = HistoryListener(model=center_state)
    sm.add_listener(the_listener)
    csms[name] = sm
    clocks[name] = asyncio.Lock()

def init_center_state_machines(centers, planners, users):
    db2 = dbset.get_central_db()
    centers_list = db2.t.center()
    names = [c.get("center_name") for c in centers_list]
    for name in names:
        add_center_state_machine(name, centers, planners, users)

# ~/~ end
# ~/~ end
