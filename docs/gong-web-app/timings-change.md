# Change timetables page

Will only be reachable for authenticated users and planner for the selected center.

```python
#| file: libs/timechan.py 

import pandas as pd
from fasthtml.common import *
import libs.utils as utils
import libs.minio as minio
import libs.timings as timings

<<delete-timetable-struct>>

```

### Delete a row in the timetable or in the structure table

```python
#| id: delete-timetable-struct

# @rt('/timings/delete_timetable_row')
def change_timetable_row(session, request, idx, new_time, dupli):
    center = session[utils.Skey.CENTER]
    timetables_df = minio.get_center_temp_df(center, "timetables")
    period_type = timetables_df.loc[int(idx), "period_type"]
    day_type = timetables_df.loc[int(idx), "day_type"]
    time = timetables_df.loc[int(idx), "time"]
    if dupli:
        if ((timetables_df["period_type"] == period_type) & (timetables_df["day_type"] == day_type) & (timetables_df["time"] == new_time)).any():
            new_timetable = timetables_df
            message = {"error": "time_already_exists", 'time': new_time}
        else:
            new_row = timetables_df.loc[int(idx)].copy()
            new_row["time"] = new_time
            new_timetable = pd.concat([timetables_df, pd.DataFrame([new_row])], ignore_index=True)
            new_timetable = new_timetable.sort_values(by=["period_type", "day_type", "time"]).reset_index(drop=True)
            message = {"success": "time_duplicated", 'new_time': new_time}
    else:
        new_timetable = timetables_df.drop(index=int(idx)).reset_index(drop=True)
        message = {"success": "time_deleted", 'time': time}
    minio.save_df_center_temp(center, "timetables", new_timetable)
    return Div(
        timings.show_center_periods(session),
        Div(timings.select_period(session, period_type, clear_show_times=False), 
            hx_swap_oob="true", id="periods-struct"),
        Div(timings.select_timetable(session, message, period_type, day_type),
            hx_swap_oob="true", id="show-times")
    )

def timetable_form(session, period_type, day_type):
    """Create a timetable form for new entries"""    
    center = session[utils.Skey.CENTER]
    gongs_df = minio.get_center_temp_df(center, "gongs")
    targets = minio.get_center_temp_df(center, "targets")["shortname"].tolist()
    return Main(
        Div( 
            Form(
                Input(type="hidden", name="period_type", value=period_type),
                Input(type="hidden", name="day_type", value=day_type),
                # Time input
                Div(Label("Time", cls="mr-2", style="width: 60px;"), 
                    Input(type="time", name="time", value="", cls="form-control",
                          required=True, style="width: 100px;"),
                    cls="flex items-center gap-2"),
                # Gong ID dropdown
                Span(Label("Gong"),
                    Select(
                        *[Option(id, value=id) for id in gongs_df['id'].unique()],
                        name="gong_id", required=True
                    )
                ),
                # Auto checkbox
                Div(Label("Auto", cls="form-check-label"),
                    Input(type="checkbox", name="auto", value="1"),
                ),
                # Targets (default to "CC")
                Span(Label("Targets"),
                    Select(
                        *[Option(target, value=target) for target in targets],
                        name="targets", multiple=True, required=True
                    )
                ),
                # Comment field
                Textarea(name="comment", rows=3, placeholder="Enter comment..."),
                Button("Save gong timing", type="submit", cls="btn btn-primary"),
                hx_post="/timings/add_timetable_row",
                hx_target="#center-periods",
            )
        )
    )

# @rt('/timings/add_timetable')
def add_timetable_row(session, request, period_type, day_type, time, gong_id, auto, targets, comment):
    center = session[utils.Skey.CENTER]
    new_data = {
        "period_type": period_type,
        "day_type": day_type,
        "time": time,
        "gong_id": int(gong_id),
        "auto": auto,
        "targets": " ".join(targets),
        "comment": comment
    }
    timetables2_df = minio.get_center_temp_df(center, "timetables")
    timetables_df = timetables2_df[~((timetables2_df["period_type"] == period_type) & \
                                     (timetables2_df["day_type"] == day_type) & (timetables2_df["time"] == time))]
    if len(timetables_df) < len(timetables2_df):
        message = {"success": "time_modified", 'time': time}
    else:        
        message = {"success": "time_inserted", 'time': time}
    timetables_df = pd.concat([timetables_df, pd.DataFrame([new_data])], ignore_index=True)
    timetables_df = timetables_df.sort_values(by=["period_type", "day_type", "time"]).reset_index(drop=True)
    minio.save_df_center_temp(center, "timetables", timetables_df)
    return Div(
        timings.show_center_periods(session),
        Div(timings.select_period(session, period_type, clear_show_times=False), 
            hx_swap_oob="true", id="periods-struct"),
        Div(timings.select_timetable(session, message, period_type, day_type), hx_swap_oob="true", id="show-times")
    )

```

