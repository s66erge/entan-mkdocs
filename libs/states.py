# ~/~ begin <<docs/gong-web-app/center_machines.md#libs/states.py>>[init]
from abc import ABC
from abc import abstractmethod
import asyncio
from myFasthtml import *
from datetime import datetime, timezone
from statemachine import State, Event, StateMachine, StateChart
import libs.dbset as dbset
import libs.transit as transit

csms = {}

# ~/~ begin <<docs/gong-web-app/center_machines.md#state-machine>>[init]
class HistoryListener:
    def __init__(self):
        self.max_size = 50
        self.sm = None
        self.entries = []

    def setup(self, sm, max_size, **kwargs):
        self.max_size = max_size
        self.sm = sm

    def after_transition(self, event, source, target):
        log = f"At {self.sm.model.get_start_time()}, {self.sm.model.get_user()} moved {self.sm.model.center_name} from {source.id} -> {target.id} on {event}"
        self.entries.append(log)
        print(log)
        if len(self.entries) > self.max_size:
            self.entries.pop(0)

def run_center_action(state_mach, action, *args, **kwargs):
    task = asyncio.create_task(action(state_mach.model.center_name, *args, **kwargs))
    transit.register_task(state_mach.model.center_name, task)
    return task

class CenterState(StateMachine):

    listeners = [HistoryListener]

    free = State("Planning free to be edited", initial=True)
    edit = State("Planning is being edited")
    wait_01 = State("Waiting for 1am at center timezone")
    transfer = State("Transferring planning to center") 
    wait_02 = State("Waiting for 2am at center timezone")
    getting_prod = State("Getting production version after center restart")
    version_check = State("Checking production version")
    w_reco_trans = State("Planning send failed, waiting for file transfer recovery")
    w_reco_prod = State("getting prod version failed, waiting for production recovery")
    w_reco_version = State("wrong_db_version, waiting for recovery")

    progress = free.to(edit) | edit.to(wait_01) | wait_01.to(transfer) | transfer.to(wait_02) \
            | wait_02.to(getting_prod) | getting_prod.to(version_check) | version_check.to(free)

    abandon_changes   = Event(edit.to(free), name='user abandon changes')
    reco_trans_done   = Event(w_reco_trans.to(wait_02), name='recovery of file transfer done')
    reco_prod_done    = Event(w_reco_prod.to(version_check), name='recovery of db in production done')
    reco_version_done = Event(w_reco_version.to(free), name='OK version of db in production')

    problem  = transfer.to(w_reco_trans) | getting_prod.to(w_reco_prod) | version_check.to(w_reco_version)

    # used only in dev mode: force to free transitions
    force_to_free = free.from_.any()

    # ACTIONS ---------------------------------

    def on_enter_version_check(self):
        run_center_action(self, transit.check_prod_version, csms)



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
        row = self.centers[self.center_name]
        self.statustart = row.status_start
        self.user = row.created_by
        return row.status if row.status else None

    def _write_state(self, value):
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
            row = self.centers[self.center_name]
            self.statustart = row.status_start if row.status_start else None
        return self.statustart

    def get_user(self):
        if self.user is None:
            row = self.centers[self.center_name]
            self.user = row.created_by
        return self.user

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center_machines.md#create-centers-sms>>[init]

def create_center_state_machines(centers):
    clocks = {}
    db2 = dbset.get_central_db()
    centers_list = db2.t.center()
    names = [c.get("center_name") for c in centers_list]
    for name in names:
        center_state = CenterDataModel(center_name=name, centers=centers)
        sm = CenterState(model=center_state, max_size=25)
        csms[name] = sm
        clocks[name] = asyncio.Lock()
    return clocks
# ~/~ end
# ~/~ begin <<docs/gong-web-app/center_machines.md#print-graph>>[init]
def states_print():
    from statemachine import State, Event, StateMachine, StateChart 
    from statemachine.contrib.diagram import quickchart_write_svg
    sm = CenterState(StateChart)
    quickchart_write_svg(sm, "images/center_machines.svg")

# ~/~ end
# ~/~ end
