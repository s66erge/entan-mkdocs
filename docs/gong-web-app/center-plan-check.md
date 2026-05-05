# Center planning page

Will only be reachable for authenticated users and planner for the selected center.

```python
#| file: libs/plancheck.py 

from fasthtml.common import *
from datetime import date
from tabulate import tabulate
import libs.utils as utils
import libs.dbset as dbset
import libs.minio as minio

<<this-center-courses>>
<<obtain-durations>>
<<check-complete-plan>>

```

```python
#| id: check-complete-plan
def check_plan(session, plan, center):
    types_with_duration = get_types_with_duration(center)
    default_period = next((t for t in types_with_duration if t.get("tags") == "X"), {}).get("period_type", "")
    period_types_in_db =  get_period_types_in_db(center)
    session[utils.Skey.PLANOK] = True
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
                if this_end_time is None or next_start_time is None:
                    row["check"] = "Missing time info"
                elif this_end_time > next_start_time:
                    if pt == default_period or next_pt == default_period:                   
                        row["check"] = "OK Time overlap"
                    else:
                        row["check"] = "CHECK Time overtap"
                else:
                    row["check"] = "OK same day"
            elif delta_days > 1:
                row["check"] = f"OK default {delta_days} days"
            else:
                row["check"] = "OK"
        if not (row["check"].startswith("OK") or row["check"].startswith("CHECK")):
            session[utils.Skey.PLANOK] = False
    return plan
```


```python
#| id: this-center-courses

def add_end_dates(plan, center):
    types_with_duration = get_types_with_duration(center)
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

def coming_center_courses(center):
    selected_db = dbset.gong_db_name(center)
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
            'source' : selected_db

        }
        for p in periods_db_center_obj  ## [3]
    ]
    sorted_periods = sorted(periods_db_center, key=lambda x: x['start_date'])
    sorted_periods_ends = add_end_dates(sorted_periods, center)
    return sorted_periods_ends, date_current_course

```

```python
#| id: obtain-durations

def get_period_types_in_db(center):
    periods_struct_df = minio.get_center_temp_df(center, "periods_struct")
    period_types_in_db = periods_struct_df['period_type'].unique()
    return period_types_in_db

def get_types_with_duration(center):
    period_types_in_db = get_period_types_in_db(center)
    periods_structs = minio.get_center_temp_list_of_dicts(center, "periods_struct")
    timetables = minio.get_center_temp_list_of_dicts(center, "timetables")
    params_from_excel = minio.params_from_excel_minio(center)
    types_duration = []
    for vt in period_types_in_db:
        item = {}
        item["period_type"] = vt
        days = [row.get("day") for row in periods_structs
                if row.get("period_type") == vt and row.get("day") is not None]
        item["duration"] = max(days) + 1
        day_0_type = next((row.get("day_type") for row in periods_structs
                 if row.get("period_type") == vt and row.get("day") == 0), None)
        times_day_0 = [row.get("time") for row in timetables
                 if row.get("period_type") == vt and row.get("day_type") == day_0_type] 
        item["time_start_first_day"] = min(times_day_0, default=None)
        last_day_type = next((row.get("day_type") for row in periods_structs
                 if row.get("period_type") == vt and row.get("day") == max(days)), None)
        times_last_day = [row.get("time") for row in timetables
                 if row.get("period_type") == vt and row.get("day_type") == last_day_type] 
        item["time_end_last_day"] = max(times_last_day, default=None)
        if not "repeat" in last_day_type :
            item["tags"] = "F"
        elif params_from_excel.get(utils.Pkey.DEFAULT_PERIOD, "") == vt:
            item["tags"] = "X"
        else:
            item["tags"] = "V"
        types_duration.append(item)
    # Sort by duration first then RE_SORT EVERYTHING by tags descending
    # this keeps the first sorting order ok for identical tags
    types_sorted = sorted(sorted(types_duration, key=lambda x: x['duration'], reverse=True), 
                        key=lambda x: x['tags'])
    return types_sorted

```
