# Center state machines

The status of a center data is managed with a state machine. The state is persisted into the center table of the central gongUsers database, using an abstract model and a database persistent model.

```{.python file=libs/states.py}
from abc import ABC
from abc import abstractmethod
from asyncio import sleep
from fastlite import *
import time
from datetime import datetime, timezone
from statemachine import State
from statemachine import StateMachine
from libs.dbset import get_central_db
from libs.utils import isa_dev_computer

<<abstract-with-persistency>>
<<db-persistent-model>>
<<state-machine>>
<<create-centers-sms>>
<<manual-testing>>
```
### The state machine for each center

see: https://python-statemachine.readthedocs.io/en/latest/index.html

```{.python #state-machine}
class CenterState(StateMachine):
    free = State(initial=True)   # free to be edited
    edit = State()               # being edited
    wait00_trans = State()       # waiting for 0am to check transfer 
    wait03_prod = State()        # waiting for 3am to check production 
    reco_trans = State()         # waiting for file transfer recovery
    reco_prod = State()          # waiting for file production recovery

    starts_editing = free.to(edit)                  # user starts editing       
    abandon_changes = edit.to(free)                 # user abandon changes
                                                     # ... just in case ...
    change_timer_done = edit.to(free)               # 1 hour countdown finished
    saving_changes = edit.to(wait00_trans)          # user saves changes
    file_trans_done = wait00_trans.to(wait03_prod)  # at 0am: file transfer by PI done
    file_not_trans = wait00_trans.to(reco_trans)    # at 0am: file transfer by PI NOT done
    reco_trans_done = reco_trans.to(wait03_prod)    # recovery of file transfer done
    db_prod_done = wait03_prod.to(free)             # at 3am: db in production done
    db_not_prod = wait03_prod.to(reco_prod)         # at 3am: db in production NOT done
    reco_prod_done = reco_prod.to(free)             # recovery of db in production done

```

# State machines creation and access

1 state machine per center.
To create them: csms = create_center_state_machines()
To access the sm for one center: sm = csms["Mahi"]

```{.python #create-centers-sms}

def create_center_state_machines(db):
    csm = {}
    db2 = get_central_db()
    centers = db2.t.centers()
    names = [c.get("center_name") for c in centers]
    for name in names:
        center_state = CenterDataModel(center_name=name, db=db)
        sm = CenterState(model=center_state)
        csm[name] = sm
        #print(f"Center: {name}, State: {sm.current_state.id}, started at: {sm.model.get_start_time()}, user: {sm.model.get_user()} ")
    return csm
```

### DBPersistentModel: Concrete model strategy

A concrete implementation of the generic storage protocol above, that reads and writes to the central database on table centers with center_name in fields:

- status: the current state
- current_user: the user who took ownership of this center database
- status_start: date/time when the status changed (ISO UTC string)

```{.python #db-persistent-model}
class CenterDataModel(AbstractPersistentModel):
    def __init__(self, center_name, db, user=None):
        super().__init__()
        self.center_name = center_name
        self.db = db
        self.user = user
        self.statustart = None  # Cache for the timestamp of the last state change

    def _read_state(self):
        centers = self.db.t.centers
        Center = centers.dataclass()
        row = centers[self.center_name]
        self.statustart = row.status_start
        self.user = row.current_user
        return row.status if row.status else None

    def _write_state(self, value):
        centers = self.db.t.centers
        # Write BOTH state AND current timestamp
        now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        self.statustart = now_utc      
        centers.update(
            center_name=self.center_name, 
            status=value,
            status_start=now_utc,
            current_user=self.user
        )

    def get_start_time(self):
        if self.statustart is None:
            # If statustart is not cached, read it from the database
            centers = self.db.t.centers
            Center = centers.dataclass()
            row = centers[self.center_name]
            self.statustart = row.status_start if row.status_start else None
        return self.statustart

    def get_user(self):
        if self.user is None:
            centers = self.db.t.centers
            Center = centers.dataclass()
            row = centers[self.center_name]
            self.user = row.current_user
        return self.user
```

# Abstract model with persistency protocol

Abstract Base Class for persistent models.
Subclasses should implement concrete strategies for:

- `_read_state`: Read the state from the concrete persistent layer.
- `_write_state`: Write the state from the concrete persistent layer.

```{.python #abstract-with-persistency}
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
```

### Let's create instances and test the persistence.

To execute only when all center status are 'free'

```{.python #manual-testing}
def states_test():
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
    sm.send("starts_editing")
    print(f"new state: {sm.current_state.id}, started at: {sm.model.get_start_time()}, user: {sm.model.get_user()}")
    # Remove the instances from memory.
    del sm
    time.sleep(3)
    print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
    db = get_central_db()
    centers = db.t.centers
    Center = centers.dataclass()
    print(f"in database: {centers['Mahi'].status}, started at: {centers['Mahi'].status_start}, user: {centers['Mahi'].current_user}")
    # Restore the previous state from db.
    time.sleep(3)
    print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
    sm = csm["Mahi"]
    print(f"State restored from database: {sm.current_state.id}, started at: {sm.model.get_start_time()}, user: {sm.model.get_user()}")
    time.sleep(3)
    print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
    sm.model.user = None
    sm.send("abandon_changes")
    print(f"State after last transition: {sm.current_state.id}, started at: {sm.model.get_start_time()}, user: {sm.model.get_user()}")
```
