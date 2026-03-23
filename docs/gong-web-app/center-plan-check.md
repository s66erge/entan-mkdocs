# Center planning page

Will only be reachable for authenticated users and planner for the selected center.

```python
#| file: libs/plancheck.py 

from fasthtml.common import *
from datetime import date
from tabulate import tabulate
import pandas as pd
import libs.utils as utils

<<this-center-courses>>
<<obtain-durations>>
<<check-complete-plan>>

```

```python
#| id: check-complete-plan
def check_plan(session, plan, selected_name, centers):
    center_obj = centers[selected_name]
    types_with_duration = get_types_with_duration(center_obj)
    _, period_types_in_db =  get_period_types_in_db(center_obj)
    print(period_types_in_db)
    session['planOK'] = True
    for idx, row in enumerate(plan):
        if idx == len(plan) - 1:
            row["check"] = "OK"
            continue
        next_start_date = plan[idx + 1].get("start_date")
        pt = row.get("period_type")
        try:
            e_this = date.fromisoformat(row.get("end_date"))
            s_next = date.fromisoformat(next_start_date) 
            delta_days = (s_next - e_this).days 
        except Exception:
            row["check"] = "InvalidDate"
        else:
            if not pt in period_types_in_db:
                row["check"] = "NoType"
            elif row.get("start_date") == next_start_date and pt == plan[idx + 1].get("period_type"):
                row["check"] = "Duplicated periods"
            elif row.get("start_date") == next_start_date:
                row["check"] = "Same starting date"
            elif delta_days < 0:
                row["check"] = f"Overlap of {- delta_days} day(s)"
            elif delta_days == 0:
                this_end_time = next((t.get("time_end_last_day") for t in types_with_duration
                                    if t.get("period_type") == pt), None)
                next_pt = plan[idx + 1].get("period_type")
                next_start_time = next((t.get("time_start_first_day") for t in types_with_duration
                                        if t.get("period_type") == next_pt), None)
                if this_end_time > next_start_time:
                    row["check"] = "CHECK Time overlap"
                else:
                    row["check"] = "OK same day"
            elif delta_days > 1:
                row["check"] = f"OK default {delta_days} days"
            else:
                row["check"] = "OK"
        if not (row["check"].startswith("OK") or row["check"].startswith("CHECK")):
            session['planOK'] = False
    return plan
```


```python
#| id: this-center-courses

def add_end_dates(plan, center_obj):
    types_with_duration = get_types_with_duration(center_obj)
    for i in range(len(plan)):
        if 'end_date' not in plan[i] or plan[i]['end_date'] is None:
            this_type = list(filter(lambda x: x.get("period_type") == plan[i]['period_type'], types_with_duration))[0]
            if this_type["tags"] != "F":
                if i < len(plan) - 1:
                    next_start = plan[i+1].get('start_date')
                    plan[i]['end_date'] = utils.add_months_days(next_start, 0, -1)
                else:
                    plan[i]['end_date'] = utils.add_months_days(plan[i]['start_date'], 0, 1)
            else:
                plan[i]['end_date'] = utils.add_months_days(plan[i]['start_date'], 0, this_type.get("duration") -1)
    return plan

def coming_center_courses(center_obj):
    #center = center_obj.center_name
    selected_db = center_obj.gong_db_name
    db_center = database(utils.get_db_path() + selected_db)

    periods = db_center.t.coming_periods
    Period = periods.dataclass()
    count_past = sum(1 for item in periods() if date.fromisoformat(item.start_date) < date.today())
    date_current_course = periods()[count_past-1].start_date  ## [2]

    periods_db_center_obj = periods()[count_past-1:]  ## [3]
    periods_db_center = [
        {
            'start_date': p.start_date,
            'period_type': p.period_type,
            'source' : f"{center_obj.center_name.lower()}_db"

        }
        for p in periods_db_center_obj  ## [3]
    ]
    sorted_periods = sorted(periods_db_center, key=lambda x: x['start_date'])
    sorted_periods_ends = add_end_dates(sorted_periods, center_obj)
    return sorted_periods_ends, date_current_course

```

```python
#| id: obtain-durations
def dict_from_excel(center, sheet):
    file_path = utils.get_db_path() + center + ".xlsx"
    df = pd.read_excel(file_path, sheet_name=sheet)
    return df.to_dict('records')

def get_period_types_in_db(center_obj):
    selected_db = center_obj.gong_db_name
    db_center = database(utils.get_db_path() + selected_db)
    period_types_in_db = set(row.get("period_type") for row in list(db_center.t.periods_struct()))
    return db_center, period_types_in_db

def get_types_with_duration(center_obj):
    db_center, period_types_in_db = get_period_types_in_db(center_obj)
    types_duration = []
    for vt in period_types_in_db:
        item = {}
        item["period_type"] = vt
        days = [row.get("day") for row in list(db_center.t.periods_struct())
                if row.get("period_type") == vt and row.get("day") is not None]
        item["duration"] = max(days) + 1
        day_0_type = next((row.get("day_type") for row in list(db_center.t.periods_struct())
                 if row.get("period_type") == vt and row.get("day") == 0), None)
        times_day_0 = [row.get("time") for row in list(db_center.t.timetables())
                 if row.get("period_type") == vt and row.get("day_type") == day_0_type] 
        item["time_start_first_day"] = min(times_day_0)
        last_day_type = next((row.get("day_type") for row in list(db_center.t.periods_struct())
                 if row.get("period_type") == vt and row.get("day") == max(days)), None)
        times_last_day = [row.get("time") for row in list(db_center.t.timetables())
                 if row.get("period_type") == vt and row.get("day_type") == last_day_type] 
        item["time_end_last_day"] = max(times_last_day)
        if "repeating" in last_day_type :
            item["tags"] = "V"
        else:
            item["tags"] = "F"
        types_duration.append(item)
    return types_duration

```
