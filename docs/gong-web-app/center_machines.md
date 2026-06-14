# Center state machines

## Synchronisation between Rasperry Pi and web program

Synchro by reading and writing files on a shared s3 server: 
- Server public endpoint : bucket-production-6009.up.railway.app:443
- Bucket : dhamma-gong-database

00h45 : Web program writes the new center gong db file in the bucket
- f"{center_name}/sending{file-ISO_date}.db"
- example: mahi/sending2024-04-09.db

01h00 : Rasperry Pi 
- reads the file if it is there
- IF the file is there
  - IF the date in the file name is today's date
    - message = f"OK: {today_ISO_date}"
    - restarts with the new db file
  - ELSE # dates do not match
    - message = f"wrong_date: {file_ISO_date}"
    - restarts on the same db as before
  - writes the message in the bucket:
    - in the file: "f"{center_name}/settings.json"
    - in a dict of dict with access key: 'general' then 'db_version'
- ELSE # no file there
  - restarts on the same db as before

01h20 : Web program
- reads the settings.json file, if there
- delete the files : .db and/or settings.json 

## State machine for center state (and data) management 

The status of a center data is managed with a state machine. The state is persisted into the center table of the central gongUsers database, using an abstract model and a database persistent model.

```python
#| file: libs/states.py

from abc import ABC
from abc import abstractmethod
import asyncio
import threading
# from fasthtml.common import *
from datetime import datetime, timezone
from statemachine import State, Event, StateChart
import libs.dbset as dbset
import libs.transit as transit
import libs.utils as utils

csms = {}
clocks = {}

<<state-machine>>
<<abstract-with-persistency>>
<<db-persistent-model>>
<<create-centers-sms>>
```
### The state machine for each center

see: https://python-statemachine.readthedocs.io/en/latest/index.html

```python
#| id: state-machine

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
    save_db = State("Saving new planning in database")
    wait_01 = State("Waiting for 1am at center timezone")
    transfer = State("Transferring planning to center") 
    wait_02 = State("Waiting for 2am at center timezone")
    getting_prod = State("Deleting production version after center restart")
    w_reco_trans = State("Planning send failed, waiting for file transfer recovery")
    w_reco_prod = State("Deleting prod version failed, waiting for production recovery")

    progress = free.to(edit) | edit.to(save_db) | save_db.to(wait_01) \
            | wait_01.to(transfer) | transfer.to(wait_02) | wait_02.to(getting_prod) \
            | getting_prod.to(free)

    abandon_changes   = Event(edit.to(free), name='user abandon changes')
    edit_timer_done   = Event(edit.to(free), name='1 hour edit timer elapsed')
    reco_trans_done   = Event(w_reco_trans.to(wait_02), name='recovery of file transfer done')
    reco_prod_done    = Event(w_reco_prod.to(free), name='recovery of db in production done')

    problem  = transfer.to(w_reco_trans) | getting_prod.to(w_reco_prod)

    # used only in dev mode: force to free transitions
    force_to_free = free.from_.any()

    # ACTIONS ---------------------------------

    def go_next(self, result, delai=1, sendid = None):
        self.model.last_result = result
        if "success" in result:
            self.send("progress", delay=delai, send_id=sendid)
            return
        else:
            self.send("problem")
            return

    def on_enter_free(self):
        self.model.last_result = {"success": "center is free again"}
        if not self.model.testing:
            self.model.clear_user()

    def on_exit_edit(self):
        self.model.last_result = None

    def on_enter_save_db(self):
        if not self.model.testing:
            result = transit.save_db_plan_times(self)
        else:
            result = {"success": "testing: on_enter_save_db"}
        return self.go_next(result)

    def on_enter_wait_01(self):
        if not self.model.testing:
            result, delay = transit.get_delay(self, utils.Globals.WAIT01_HOUR , utils.Globals.WAIT01_MINS)
        else:
            delay = self.test_delay
            result = {"success": f"testing: on_enter_wait_01 with delay: {self.test_delay}"}
        self.model.send_id = f"{self.model.center_name}_wait01"
        print(f"delay {delay}")
        return self.go_next(result, delay, self.model.send_id)

    def on_exit_wait_01(self):
        if self.model.send_id:
            print("Canceling delayed event ", self.model.send_id)
            self.cancel_event(self.model.send_id)

    def on_enter_transfer(self):
        if not self.model.testing:
            result = transit.transfer_new_db(self)
        else:
            result = {"success": "testing: on_enter_transfer"}
            print("'Enter' for 'success', anything for 'error'")
            if input("?"):
                result = {"error": f"{result["success"]}"}
        return self.go_next(result)

    def on_enter_wait_02(self):
        if not self.model.testing:
            result, delay = transit.get_delay(self, utils.Globals.WAIT02_HOUR , utils.Globals.WAIT02_MINS)
        else:
            delay = self.test_delay
            result = {"success": f"testing: on_enter_wait_02 with delay: {self.test_delay}"}
        self.model.send_id = f"{self.model.center_name}_wait02"        
        return self.go_next(result, delay, self.model.send_id)

    def on_exit_wait_02(self):
        if self.model.send_id:
            print("Canceling delayed event ", self.model.send_id)
            self.cancel_event(self.model.send_id)

    def on_enter_getting_prod(self):
        if not self.model.testing:
            result = transit.delete_new_db(self)
        else:
            result = {"success": "testing: on_enter_getting_prod"}
            print("'Enter' for 'success', anything for 'error'")
            if input("?"):
                result = {"error": f"{result["success"]}"}
        return self.go_next(result)

```

1. an annotation

### State machines creation and access

1 state machine per center.
To create them: csms = init_center_state_machines()
To access the sm for one center: sm = csms["Mahi"]

```python
#| id: create-centers-sms

def delete_state_machine(center_name):
    del csms[center_name]
    del clocks[center_name]

def add_center_state_machine(name, centers):
    center_state = CenterDataModel(center_name=name, centers=centers)
    sm = CenterState(model=center_state)
    the_listener = HistoryListener(model=center_state)
    sm.add_listener(the_listener)
    csms[name] = sm
    clocks[name] = threading.Lock()

def init_center_state_machines(centers):
    db2 = dbset.get_central_db()
    centers_list = db2.t.center()
    names = [c.get("center_name") for c in centers_list]
    for name in names:
        add_center_state_machine(name, centers)

```

### DBPersistentModel: Concrete model strategy

A concrete implementation of the generic storage protocol above, that reads and writes to the central database on table centers with center_name in fields:

- status: the current state
- created_by: the user who took ownership of this center database
- status_start: date/time when the status changed (ISO UTC string)

```python
#| id: db-persistent-model
class CenterDataModel(AbstractPersistentModel):
    def __init__(self, center_name, centers, testing=False, user=None):
        super().__init__()
        self.center_name = center_name
        self.centers = centers
        self.testing = testing
        self.user = user
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
        return row.status if row.status else None

    def _write_state(self, value):
        # Write BOTH state AND current timestamp
        now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        self.statustart = now_utc      
        self.centers.update(
            center_name = self.center_name, 
            status = value,
            status_start = now_utc,
            created_by = self.user
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

    def clear_user(self):
        self.centers.update(
            center_name = self.center_name, 
            created_by = None
        )

```

# Abstract model with persistency protocol

Abstract Base Class for persistent models.
Subclasses should implement concrete strategies for:

- `_read_state`: Read the state from the concrete persistent layer.
- `_write_state`: Write the state from the concrete persistent layer.

```python
#| id: abstract-with-persistency
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
