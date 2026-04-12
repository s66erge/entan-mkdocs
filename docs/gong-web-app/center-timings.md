# Timetables page

Will only be reachable for authenticated users and planner for the selected center.

```python
#| file: libs/timings.py 

import asyncio
import json
import os
import shutil
import pandas as pd
from tabulate import tabulate
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import quote_plus
from fasthtml.common import *
import libs.utils as utils
import libs.cdash as cdash 
import libs.plancheck as plancheck
import libs.fetch as fetch
import libs.dbset as dbset
import libs.minio as minio
import libs.utilsJS as utilsJS


<<check-show-period-types>>
<<load-save-timings>>
<<show-struct-timetable>>
<<delete-timetable-struct>>

```

### Load and save timetables

```python
#| id: load-save-timings

def load_timings(session):
    center = session[utils.Skey.CENTER]
    selected_db = dbset.gong_db_name(center)
    table = plancheck.get_types_with_duration(center)
    center_periods_df = pd.DataFrame(table)
    minio.save_df_center_temp(center, "center_periods", center_periods_df)
    db_center = database(utils.get_db_path() + selected_db)
    periods_struct_df = pd.DataFrame(list(db_center.t.periods_struct()))
    minio.save_df_center_temp(center, "periods_struct", periods_struct_df) 
    gongs_df = pd.DataFrame(list(db_center.t.gongs()))
    minio.save_df_center_temp(center, "gongs", gongs_df) 
    targets_df = pd.DataFrame(list(db_center.t.targets()))
    minio.save_df_center_temp(center, "targets", targets_df)
    timetables_df = pd.DataFrame(list(db_center.t.timetables()))
    minio.save_df_center_temp(center, "timetables", timetables_df)
    return

```


### Period types 

```python
#| id: check-show-period-types

# @rt('/timings/load_center_periods')
def show_center_periods(session):
    center = session[utils.Skey.CENTER]
    center_periods_df = minio.get_center_temp_df(center, "center_periods")
    center_periods_df["Actions"] = center_periods_df['period_type'].apply(
        lambda pt: A("Select",
            hx_get=f"/timings/select_period?period_type={quote_plus(pt)}",
            hx_target="#periods-struct"
        )
    )
    html_periods = center_periods_df.to_html(index=False, escape=False)
    errors_df = check_timings(session)
    html_errors = errors_df.to_html(index=False) if not errors_df.empty else None
    return Div(
        Div("",hx_swap_oob="true",id="show-timetables"),
        H2("Center periods"),
        Div("",hx_swap_oob="true",id="planning-periods"),
        Div(Safe(html_periods)),
        Div(H3("Timing errors"),
            Safe(html_errors)) if html_errors else None,
        Div(id="periods-struct"),
        Div(id="show-timetables"),

    )

def check_timings(session):
    center = session[utils.Skey.CENTER]
    center_periods_df = minio.get_center_temp_df(center, "center_periods")
    periods_struct_df = minio.get_center_temp_df(center, "periods_struct")
    gongs_df = minio.get_center_temp_df(center, "gongs")
    targets_df = minio.get_center_temp_df(center, "targets")
    timetables_df = minio.get_center_temp_df(center, "timetables")

    errors_df = pd.DataFrame(columns=["period_type", "error", "day_type", "time", "gong_id", "targets"])

    day_number_sets_for_period_types_dict = (
    periods_struct_df.groupby("period_type")["day"]
       .apply(set)
       .to_dict()
    )
    for period_type, day_numbers in day_number_sets_for_period_types_dict.items():
        if 0 not in day_numbers:
            errors_df.loc[len(errors_df)] = {
                "period_type": period_type,
                "error": "No day 0"
            }
        if max(day_numbers) - min(day_numbers) + 1 != len(day_numbers):
            errors_df.loc[len(errors_df)] = {
                "period_type": period_type,
                "error": "Non-consecutive day numbers"
            }

    # Build a set of valid pairs from timetables_df
    valid_pairs = set(zip(timetables_df["period_type"], timetables_df["day_type"]))
    # Build the pairs from periods_struct_df
    pairs = list(zip(periods_struct_df["period_type"], periods_struct_df["day_type"]))
    # Mask: True when the pair does NOT exist in timetables_df
    mask = [p not in valid_pairs for p in pairs]
    # Extract invalid rows
    invalid_day_types = periods_struct_df.loc[mask, ["period_type", "day_type"]]
    invalid_day_types["error"] = "No timetable entry for this day type"

    invalid_gongs = timetables_df.loc[~timetables_df["gong_id"].isin(gongs_df["id"]),
                           ["period_type", "day_type", "time", "gong_id"]]    
    invalid_gongs["error"] = "Invalid gong_id"

    valid_targets = set(targets_df["shortname"])
    invalid_targets = timetables_df.loc[
        ~timetables_df["targets"].str.split().apply(lambda t: set(t).issubset(valid_targets)),
        ["period_type", "day_type", "time", "targets"]
    ]
    invalid_targets["error"] = "At least one invalid target"

    errors_df = pd.concat([errors_df, invalid_day_types, invalid_gongs,invalid_targets], ignore_index=True)
    errors2_df = errors_df.fillna("")
    errors2_df["gong_id"] = errors2_df["gong_id"].apply(
        lambda x: int(x) if isinstance(x, float) and pd.notna(x) else ""
    )
    return errors2_df
```

### Show the selected structure table and a selected timetable

```python
#| id: show-struct-timetable

# @rt('/timings/select_period')
def select_period(session, period_type):
    center = session[utils.Skey.CENTER]
    periods_struct_df = minio.get_center_temp_df(center, "periods_struct")
    filtered = periods_struct_df[periods_struct_df["period_type"] == period_type]
    filtered["Actions"] = filtered['day_type'].apply(
        lambda dt: A("Select",
            hx_get=f"/timings/select_timetable?period_type={quote_plus(period_type)}&day_type={quote_plus(dt)}",
            hx_target="#show-timetables"
        )
    )
    html_struct = filtered.to_html(index=False, escape=False)
    return Div(
        Div("",hx_swap_oob="true",id="show-timetables"),
        H3(f"Structure for period type: '{period_type}'"),
        Safe(html_struct),
    )

# @rt('/timings/select_timetable')
def select_timetable(session, period_type, day_type):
    center = session[utils.Skey.CENTER]
    timetables_df = minio.get_center_temp_df(center, "timetables")
    timetables_df["Actions"] = timetables_df.index.to_series().apply(
        lambda idx: A("Delete",
            hx_get=f"/timings/delete_timetable_row?idx={idx}",
            hx_target="#timetables"
        )
    )
    filtered = timetables_df[
        (timetables_df["period_type"] == period_type) &
        (timetables_df["day_type"] == day_type)]
    html_timetables = filtered.to_html(index=False, escape=False)
    return Div(
        H3(f"Timetable for day type: '{day_type}' in period type: '{period_type}'"),
        Safe(html_timetables)
    )

```

### Delete a row in the timetable or in the structure table

```python
#| id: delete-timetable-struct

# @rt('/timings/delete_timetable_row')
def delete_timetable_row(session, request):
    params = dict(request.query_params)
    idx = params.get("idx")
    center = session[utils.Skey.CENTER]
    timetables_df = minio.get_center_temp_df(center, "timetables")
    period_type = timetables_df.loc[int(idx), "period_type"]
    day_type = timetables_df.loc[int(idx), "day_type"]
    new_timetable = timetables_df.drop(index=int(idx)).reset_index(drop=True)
    minio.save_df_center_temp(center, "timetables", new_timetable)
    return Div(
        #Div("",hx_swap_oob="true",id="show-timetables"),
        Div("",hx_swap_oob="true",id="periods-struct"),
        show_center_periods(session),
        select_period(session, period_type)
    )

```

