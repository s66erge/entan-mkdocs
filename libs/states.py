# ~/~ begin <<docs/gong-web-app/center_machines.md#libs/states.py>>[init]
from abc import ABC
from abc import abstractmethod
import asyncio
from myFasthtml import *
import time
from datetime import datetime, timezone
# from statemachine import State, Event,StateMachine # moved to "myFasthtml.py"
from libs.dbset import get_central_db
from libs.utils import isa_dev_computer

# ~/~ begin <<docs/gong-web-app/center_machines.md#state-machine>>[init]
class CenterState(StateMachine):
    free = State(initial=True)   # free to be edited
    edit = State()               # being edited
    w01_trans = State()          # waiting for 1am to do/check transfer 
    w02_prod = State()           # waiting for 2am to check production 
    reco_trans = State()         # waiting for file transfer recovery
    reco_prod = State()          # waiting for production recovery

    start_editing     = Event(free.to(edit), name='user starts editing')       
    abandon_changes   = Event(edit.to(free), name='user abandon changes')
    change_timer_done = Event(edit.to(w01_trans), name='1 hour countdown finished')
    saving_changes    = Event(edit.to(w01_trans), name='user saves changes')
    file_trans_done   = Event(w01_trans.to(w02_prod), name='at 1am: file transfer by PI done')
    file_not_trans    = Event(w01_trans.to(reco_trans), name='at 1am: file transfer by PI NOT done')
    reco_trans_done   = Event(reco_trans.to(w02_prod), name='recovery of file transfer done')
    db_prod_done      = Event(w02_prod.to(free), name='at 2am: db in production done')
    db_not_prod       = Event(w02_prod.to(reco_prod), name='at 2am: db in production NOT done')
    reco_prod_done    = Event(reco_prod.to(free), name='recovery of db in production done')
    # used only in dev mode: force to free transitions
    force_to_free = free.to(free) | edit.to(free) |  w01_trans.to(free) | w02_prod.to(free)

    def on_enter_state(self, target, event):
        print(f"{self.model.user} entered {self.model.center_name} into '{target.id}' on '{event.name}'")

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
class CenterDataModel(AbstractPersistentModel):
    def __init__(self, center_name, centers, user=None):
        super().__init__()
        self.center_name = center_name
        self.centers = centers
        self.user = user
        self.statustart = None  # Cache for the timestamp of the last state change

    def _read_state(self):
        #centers = self.db.t.centers
        #Center = centers.dataclass()
        row = self.centers[self.center_name]
        self.statustart = row.status_start
        self.user = row.created_by
        return row.status if row.status else None

    def _write_state(self, value):
        #centers = self.db.t.centers
        # Write BOTH state AND current timestamp
        now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        self.statustart = now_utc      
        self.centers.update(
            center_name=self.center_name, 
            status=value,
            status_start=now_utc,
            created_by=self.user
        )

    def get_start_time(self):
        if self.statustart is None:
            # If statustart is not cached, read it from the database
            #centers = self.db.t.centers
            #Center = centers.dataclass()
            row = self.centers[self.center_name]
            self.statustart = row.status_start if row.status_start else None
        return self.statustart

    def get_user(self):
        if self.user is None:
            #centers = self.db.t.centers
            #Center = centers.dataclass()
            row = self.centers[self.center_name]
            self.user = row.created_by
        return self.user

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center_machines.md#create-centers-sms>>[init]

def create_center_state_machines(centers):
    csms = {}
    clocks = {}
    db2 = get_central_db()
    centers_list = db2.t.center()
    names = [c.get("center_name") for c in centers_list]
    for name in names:
        center_state = CenterDataModel(center_name=name, centers=centers)
        sm = CenterState(model=center_state)
        csms[name] = sm
        clocks[name] = asyncio.Lock()
        #print(f"Center: {name}, State: {sm.current_state.id}, started at: {sm.model.get_start_time()}, user: {sm.model.get_user()} ")
    return csms, clocks
# ~/~ end
# ~/~ begin <<docs/gong-web-app/center_machines.md#manual-testing>>[init]
def states_test(centers):
    csm = create_center_state_machines()
    sm = csm["Mahi"]

    if isa_dev_computer():
        from statemachine.contrib.diagram import quickchart_write_svg
        quickchart_write_svg(sm, "images/center_machines.svg") 

    print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
    print(f"Initial state: {sm.current_state.id}, started at: {sm.model.get_start_time()}, user: {sm.model.get_user()}")
    time.sleep(3)
    print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
    sm.model.user = "abc@mail.com"
    sm.send("start_editing")
    print(f"new state: {sm.current_state.id}, started at: {sm.model.get_start_time()}, user: {sm.model.get_user()}")
    # Remove the instances from memory.
    del sm
    time.sleep(3)
    print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
    #db = get_central_db()
    #centers = db.t.centers
    #Center = centers.dataclass()
    print(f"in database: {centers['Mahi'].status}, started at: {centers['Mahi'].status_start}, user: {centers['Mahi'].created_by}")
    # Restore the previous state from db
    time.sleep(3)
    print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
    sm = csm["Mahi"]
    print(f"State restored from database: {sm.current_state.id}, started at: {sm.model.get_start_time()}, user: {sm.model.get_user()}")
    time.sleep(3)
    print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
    sm.model.user = None
    sm.send("abandon_changes")
    print(f"State after last transition: {sm.current_state.id}, started at: {sm.model.get_start_time()}, user: {sm.model.get_user()}")
# ~/~ end
# ~/~ end
