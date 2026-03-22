# Let's create instances and test the persistence.
# To execute only when all center status are 'free'

from fasthtml.common import *
import time
from datetime import datetime, timezone
from libs.utils import isa_dev_computer
from libs.states import create_center_state_machines

def states_test(centers):
    csm = create_center_state_machines()
    sm = csm["Mahi"]

    if isa_dev_computer():
        from statemachine.contrib.diagram import quickchart_write_svg
        quickchart_write_svg(sm, "images/center_machines.svg") 

    print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
    print(f"Initial state: {sm.configuration[0].id}, started at: {sm.model.get_start_time()}, user: {sm.model.get_user()}")
    time.sleep(3)
    print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
    sm.model.user = "abc@mail.com"
    sm.send("start_editing")
    print(f"new state: {sm.configuration[0].id}, started at: {sm.model.get_start_time()}, user: {sm.model.get_user()}")
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
    print(f"State restored from database: {sm.configuration[0].id}, started at: {sm.model.get_start_time()}, user: {sm.model.get_user()}")
    time.sleep(3)
    print(datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S+00:00'))
    sm.model.user = None
    sm.send("abandon_changes")
    print(f"State after last transition: {sm.configuration[0].id}, started at: {sm.model.get_start_time()}, user: {sm.model.get_user()}")
