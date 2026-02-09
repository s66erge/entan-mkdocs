"""
Persistent domain model
=======================

An example originated from a question: "How to save state to disk?". There are many ways to
implement this, but you can get an insight of one possibility. This example implements a custom
domain model that persists it's state using a generic strategy that can be extended to any storage
format.

Original `issue <https://github.com/fgmacedo/python-statemachine/issues/358>`_.


Resource management state machine
---------------------------------

Given a simple on/off machine for resource management.

"""

from abc import ABC
from abc import abstractmethod
from asyncio import sleep
from fastlite import *
import time
from datetime import datetime, timezone
from statemachine import State
from statemachine import StateMachine
from libs import dbset
from libs import utils

class CenterState(StateMachine):
    free = State(initial=True)   # free to be edited
    edit = State()               # being edited
    wait00_trans = State()       # waiting for 0am to check transfer 
    wait03_prod = State()        # waiting for 3am to check production 
    reco_trans = State()         # waiting for file transfer recovery
    reco_prod = State()          # waiting for file production recovery

    starts_editing = free.to(edit)                  # user starts editing       
    abandon_changes = edit.to(free)                 # user abandon changes
    change_timer_done = edit.to(free)               # 1 hour countdown finished
    saving_changes = edit.to(wait00_trans)          # user saves changes
    file_trans_done = wait00_trans.to(wait03_prod)  # at 0am: file transfer by PI done
    file_not_trans = wait00_trans.to(reco_trans)    # at 0am: file transfer by PI NOT done
    reco_trans_done = reco_trans.to(wait03_prod)    # recovery of file transfer done
    db_prod_done = wait03_prod.to(free)             # at 3am: db in production done
    db_not_prod = wait03_prod.to(reco_prod)         # at 3am: db in production NOT done
    reco_prod_done = reco_prod.to(free)             # recovery of db in production done

# %%
# Abstract model with persistency protocol
# ----------------------------------------
#
# Abstract Base Class for persistent models.
# Subclasses should implement concrete strategies for:
#
# - `_read_state`: Read the state from the concrete persistent layer.
# - `_write_state`: Write the state from the concrete persistent layer.


class AbstractPersistentModel(ABC):
    """Abstract Base Class for persistent models.

    Subclasses should implement concrete strategies for:

    - `_read_state`: Read the state from the concrete persistent layer.
    - `_write_state`: Write the state from the concrete persistent layer.
    """

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


# %%
# DBPersistentModel: Concrete model strategy
# --------------------------------------------
#
# A concrete implementation of the generic storage protocol above, that reads and writes
# to the central database on table centers with center_name in field status.

class DBPersistentModel(AbstractPersistentModel):
    """A concrete implementation of a storage strategy for a Model
    that reads and writes to a file.
    """

    def __init__(self, center_name):
        super().__init__()
        self.center_name = center_name
        self.statustart = None  # Cache for the timestamp of the last state change

    def _read_state(self):
        db = dbset.get_central_db()
        centers = db.t.centers
        Center = centers.dataclass()
        row = centers[self.center_name]
        return row.status if row.status else None

    def _write_state(self, value):
        db = dbset.get_central_db()
        centers = db.t.centers
        # Write BOTH state AND current timestamp
        now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00')
        self.statustart = now_utc      
        centers.update(
            center_name=self.center_name, 
            status=value,
            status_start=now_utc
        )


# %%
# Let's create instances and test the persistence.

def create_center_state_machines():
    csm = {}
    db = dbset.get_central_db()
    centers = db.t.centers()
    names = [c.get("center_name") for c in centers]
    print(f"Centers in database: {names}")
    for name in names:
        center_state = DBPersistentModel(center_name=name)
        sm = CenterState(model=center_state)
        csm[name] = sm
        print(f"Center: {name}, State: {sm.current_state.id}")
    return csm

csm = create_center_state_machines()

sm = csm["Mahi"]

if utils.isa_dev_computer():
    from statemachine.contrib.diagram import quickchart_write_svg
    quickchart_write_svg(sm, "images/center_machines.svg") 

print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
print(f"Initial state: {sm.current_state.id}")
time.sleep(3)

print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
sm.send("starts_editing")

print(f"new state: {sm.current_state.id}, started at: {sm.model.statustart}")

# Remove the instances from memory.
del sm

time.sleep(3)
print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
db = dbset.get_central_db()
centers = db.t.centers
Center = centers.dataclass()
print(f"in database: {centers['Mahi'].status}", centers['Mahi'].status_start)

# Restore the previous state from db.

time.sleep(3)
print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
sm = csm["Mahi"]

print(f"State restored from database: {sm.current_state.id}, started at: {sm.model.statustart}")

time.sleep(3)
print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
sm.send("abandon_changes")

print(f"State after last transition: {sm.current_state.id}, started at: {sm.model.statustart}")