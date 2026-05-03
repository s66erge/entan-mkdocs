# Change timetables page

Will only be reachable for authenticated users and planner for the selected center.

```python
#| file: libs/timechan.py 

import pandas as pd
from fasthtml.common import *
from wcwidth import center
import libs.utils as utils
import libs.minio as minio
import libs.timings as timings
import libs.messages as messages

<<repaint-timings>>
<<change-timetables>>
<<change-struct>>
<<create-period>>

```

### Copy period from a center

```python
#| id: create-period

# @rt('/timings/create_new_period')
def create_new_period(session, from_center, new_period, from_period):
    this_center = session[utils.Skey.CENTER]
    this_center_periods_df = minio.get_center_temp_df(this_center, "center_periods")
    if new_period in this_center_periods_df["period_type"].values:
        day_type = ""
        message = {"error": "period_already_exists"}
    else:
        timings.load_timings(from_center)
        from_center_periods_df = minio.get_center_temp_df(from_center, "center_periods")
        new_rows = from_center_periods_df[from_center_periods_df["period_type"] == from_period].copy()
        new_rows["period_type"] = new_period
        this_center_periods_df = pd.concat([this_center_periods_df, new_rows], ignore_index=True)
        this_center_periods_df = this_center_periods_df.sort_values(by=["tags", "period_type"]).reset_index(drop=True)
        minio.save_df_center_temp(this_center, "center_periods", this_center_periods_df)

        this_center_struct_df = minio.get_center_temp_df(this_center, "periods_struct")
        from_center_struct_df = minio.get_center_temp_df(from_center, "periods_struct")
        new_rows = from_center_struct_df[from_center_struct_df["period_type"] == from_period].copy()
        new_rows["period_type"] = new_period
        this_center_struct_df = pd.concat([this_center_struct_df, new_rows], ignore_index=True)
        this_center_struct_df = this_center_struct_df.sort_values(by=["period_type", "day"]).reset_index(drop=True)
        minio.save_df_center_temp(this_center, "periods_struct", this_center_struct_df)

        this_center_timetables_df = minio.get_center_temp_df(this_center, "timetables")
        from_center_timetables_df = minio.get_center_temp_df(from_center, "timetables")
        new_rows = from_center_timetables_df[from_center_timetables_df["period_type"] == from_period].copy()
        new_rows["period_type"] = new_period
        params = minio.params_from_excel_minio(this_center)
        new_rows["gong_id"] = params[utils.Pkey.GONG_ID]
        new_rows["targets"] = params[utils.Pkey.TARGETS]
        this_center_timetables_df = pd.concat([this_center_timetables_df, new_rows], ignore_index=True)
        this_center_timetables_df = this_center_timetables_df.sort_values(by=["period_type", "day_type", "time"]).reset_index(drop=True)
        minio.save_df_center_temp(this_center, "timetables", this_center_timetables_df)

        day_type = new_rows.iloc[0]["day_type"]
        message = {"success": "period_created"}
    return repaint(session, new_period, day_type, message, False)

```

### Repaint the timings page

```python
#| id: repaint-timings

def repaint(session, period_type, day_type, message, clear_show_times):
    return Div(
        Div(
            Div(timings.show_center_periods(session),
                hx_swap_oob="true", id="center_periods"),
            Div(timings.select_period(session, period_type, clear_show_times), 
                hx_swap_oob="true", id="periods-struct"),
            Div(timings.select_timings(session, period_type, day_type),
                hx_swap_oob="true", id="show-times")
        ) if message.get("success") else None,
        Div(messages.feedback_to_user(message))
    )

```

### Modify structures

```python
#| id: change-struct

# @rt('/timings/modify_day_type')
def modify_day_type(session, index, day_type):
    center = session[utils.Skey.CENTER]
    periods_struct_df = minio.get_center_temp_df(center, "periods_struct")
    period_type = periods_struct_df.loc[index, "period_type"]
    old_day_type = periods_struct_df.loc[index, "day_type"]
    timetables_df = minio.get_center_temp_df(center, "timetables")
    if old_day_type == day_type:
        message = {"error": "day_type_unchanged"}
    else:
        message = {"success": "day_type_changed"}
        periods_struct_df.loc[index, "day_type"] = day_type
        minio.save_df_center_temp(center, "periods_struct", periods_struct_df)
    return repaint(session, period_type, day_type, message, False)

# @rt('/timings/del_last_day')
def del_last_day(session, idx):
    center = session[utils.Skey.CENTER]
    periods_struct_df = minio.get_center_temp_df(center, "periods_struct")
    period_type = periods_struct_df.loc[idx, "period_type"]
    day_type = periods_struct_df.loc[idx-1, "day_type"]
    periods_struct_df = periods_struct_df.drop(index=int(idx)).reset_index(drop=True)
    message = {"success": "last_day_deleted"}
    minio.save_df_center_temp(center, "periods_struct", periods_struct_df)
    return repaint(session, period_type, day_type, message, False)

# @rt('/timings/dup_last_day')
def dup_last_day(session, idx):
    center = session[utils.Skey.CENTER]
    periods_struct_df = minio.get_center_temp_df(center, "periods_struct")
    period_type = periods_struct_df.loc[idx, "period_type"]
    day_type = periods_struct_df.loc[idx, "day_type"]
    row = periods_struct_df.loc[[idx]]
    day = periods_struct_df.loc[idx, "day"]
    periods_struct_df = pd.concat([periods_struct_df.iloc[:idx+1], row,
                                   periods_struct_df.iloc[idx+1:]])
    periods_struct_df = periods_struct_df.reset_index(drop=True)
    periods_struct_df.loc[idx+1, "day"] = day + 1
    message = {"success": "last_day_duplicated"}
    minio.save_df_center_temp(center, "periods_struct", periods_struct_df)
    return repaint(session, period_type, day_type, message, False)

def renumber_days_df(periods_struct_df, period_type):
    # Renumber the 'day' column incrementally from 0 for rows with given period_type.
    mask = periods_struct_df["period_type"] == period_type
    periods_struct_df.loc[mask, "day"] = range(mask.sum())
    return periods_struct_df

# @rt('/timings/renumber_days')
def renumber_days(session, period_type):
    center = session[utils.Skey.CENTER]
    periods_struct_df = minio.get_center_temp_df(center, "periods_struct")
    filtered = periods_struct_df[periods_struct_df["period_type"] == period_type] 
    period_type = filtered.iloc[-1]["period_type"]
    day_type = filtered.iloc[-1]["day_type"]
    periods_struct_df = renumber_days_df(periods_struct_df, period_type)
    message = {"success": "days_renumbered"}
    minio.save_df_center_temp(center, "periods_struct", periods_struct_df)
    return repaint(session, period_type, day_type, message, False)

# @rt('/timings/create_day_type')
def create_day_type(session, period_type, new_day_type, day_type):
    center = session[utils.Skey.CENTER]
    timetables_df_bef = minio.get_center_temp_df(center, "timetables")
    all_day_types = timetables_df_bef[timetables_df_bef["period_type"] == period_type]['day_type'].unique()
    if new_day_type in all_day_types:
        message = {"error": "day_type_already_exists"}
    else:
        filtered = timetables_df_bef[(timetables_df_bef["period_type"] == period_type) &
                                     (timetables_df_bef["day_type"] == day_type)]
        filtered["day_type"] = new_day_type
        timetables_df = pd.concat([timetables_df_bef, filtered], ignore_index=True)
        timetables_df = timetables_df.sort_values(by=["period_type", "day_type", "time"]).reset_index(drop=True)
        minio.save_df_center_temp(center, "timetables", timetables_df)
        message = {"success": "day_type_created"}   
    return repaint(session, period_type, new_day_type, message, False)

```


### Modify timetables

```python
#| id: change-timetables

# @rt('/timings/delete_timetable_row')
def delete_timetable_row(session, idx):
    center = session[utils.Skey.CENTER]
    timetables_df = minio.get_center_temp_df(center, "timetables")
    period_type = timetables_df.loc[int(idx), "period_type"]
    day_type = timetables_df.loc[int(idx), "day_type"]
    filtered_timings = timetables_df[(timetables_df["period_type"] == period_type) &
                             (timetables_df["day_type"] == day_type)]
    periods_struct_df = minio.get_center_temp_df(center, "periods_struct")
    filtered_struct = periods_struct_df[(periods_struct_df["period_type"] == period_type) &
                                       (periods_struct_df["day_type"] == day_type)]
    if len(filtered_timings) == 1 and len(filtered_struct) >= 1:
        message = {"error": "delete_last_time"}
    else:
        time = timetables_df.loc[int(idx), "time"]    
        new_timetable = timetables_df.drop(index=int(idx)).reset_index(drop=True)
        message = {"success": "time_deleted", 'time': time}
        minio.save_df_center_temp(center, "timetables", new_timetable)
    return repaint(session, period_type, day_type, message, False)

# @rt('/timings/load_timing_form')
def load_timing_form(session, idx):
    """Load and display a pre-populated timetable form for modifying an existing entry"""
    center = session[utils.Skey.CENTER]
    timetables_df = minio.get_center_temp_df(center, "timetables")
    gongs_df = minio.get_center_temp_df(center, "gongs")
    targets_df = minio.get_center_temp_df(center, "targets")

    row = timetables_df.loc[int(idx)]
    period_type = row["period_type"]
    day_type = row["day_type"]
    time_value = row["time"]
    gong_id = row["gong_id"]
    auto_checked = row.get("auto") == 1 
    targets_str = row.get("targets", "")
    comment = row.get("comment", "")

    targets_list = targets_str.split() if isinstance(targets_str, str) else []
    all_targets = sorted(targets_df["shortname"].tolist())
    gong_ids = gongs_df['id'].unique()
    return Main(
        Div(
            Form(
                Input(type="hidden", name="period_type", value=period_type),
                Input(type="hidden", name="day_type", value=day_type),
                Input(type="hidden", name="idx", value=idx),
                Div(Label("Time", cls="mr-2", style="width: 60px;"), 
                    Input(type="time", name="time", value=time_value, cls="form-control",
                          required=True, style="width: 250px;"),
                    cls="flex items-center gap-2"),
                Span(Label("Gong"),
                    Select(
                        *[utils.option_selected_one(id, gong_id) for id in gong_ids],
                        name="gong_id", required=True
                    )
                ),
                Div(Label("Auto", cls="form-check-label"),
                    Input(type="checkbox", name="auto", value="1",
                          **({"checked": True} if auto_checked else {}))
                ),
                Span(Label("Targets"),
                    Select(
                        *[utils.option_selected_multi(target, targets_list) for target in all_targets],
                        name="targets", multiple=True, required=True
                    )
                ),
                Textarea(comment, name="comment", rows=3, placeholder="Enter comment..."),
                Button("Update gong timing", type="submit"),
                hx_post="/timings/add_mod_timetable_row",
                hx_target="#feedback-times",
            )
        )
    )

# @rt('/timings/add_mod_timetable_row')
def add_mod_timetable_row(session, period_type, day_type, idx, time, gong_id, auto, targets, comment):
    center = session[utils.Skey.CENTER]
    new_data = {
        "period_type": period_type,
        "day_type": day_type,
        "time": time,
        "gong_id": int(gong_id),
        "auto": 1 if auto == "1" else 0,
        "targets": " ".join(sorted(targets)),
        "comment": comment
    }
    timetables_df_bef = minio.get_center_temp_df(center, "timetables")
    if idx != -1:
        old_data = timetables_df_bef.loc[int(idx)].to_dict()
        old_time = old_data["time"]
    else:
        old_time = "00:00" # Default old time for forced new entries
    indexs_new_data = timetables_df_bef[(timetables_df_bef["period_type"] == period_type) &
                                     (timetables_df_bef["day_type"] == day_type) &
                                     (timetables_df_bef["time"] == time)].index
    index_new_data = indexs_new_data[0] if len(indexs_new_data) > 0 else None

    if index_new_data and new_data["time"] != old_time:
        # This is a modification that changes the time to an existing time (conflict)
        message = {"error": "time_already_exists", 'time': time}
    else:
        if index_new_data and new_data["time"] == old_time:
            # This is a modification of the same entry (time unchanged)
            timetables_df = timetables_df_bef.drop(index=int(idx)).reset_index(drop=True)
            message = {"success": "time_modified", 'time': time}
        else:
            # This is an insertion of a new time (no conflict)
            timetables_df = timetables_df_bef
            message = {"success": "time_inserted", 'time': time}
        timetables_df = pd.concat([timetables_df, pd.DataFrame([new_data])], ignore_index=True)
        timetables_df = timetables_df.sort_values(by=["period_type", "day_type", "time"]).reset_index(drop=True)
        minio.save_df_center_temp(center, "timetables", timetables_df)
    return repaint(session, period_type, day_type, message, False)

```
