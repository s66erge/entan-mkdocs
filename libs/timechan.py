# ~/~ begin <<docs/gong-web-app/timings-change.md#libs/timechan.py>>[init]

import pandas as pd
from fasthtml.common import *
import libs.utils as utils
import libs.minio as minio
import libs.timings as timings

# ~/~ begin <<docs/gong-web-app/timings-change.md#change-struct>>[init]

# @rt('/timings/change_day_type')
def change_day_type(session, index, day_type):
    return
"""
def change_day_type(session, index, day_type):
    center = session[utils.Skey.CENTER]
    periods_struct_df = minio.get_center_temp_df(center, "periods_struct")
    period_type = periods_struct_df[index, "period_type"]
    old_day_type = periods_struct_df[index, "day_type"]
    timetables_df = minio.get_center_temp_df(center, "timetables")
    all_day_types = timetables_df[timetables_df["period_type"] == period_type]['day_type'].unique()
    if old_day_type == day_type:
        message = {"error": "day_type_unchanged"}
    else:
        periods_struct_df[index, "day_type"] = day_type
        if day_type in list(all_day_types):
            message = {"success": "day_type_changed"}
        else:


    return
"""
# ~/~ end
# ~/~ begin <<docs/gong-web-app/timings-change.md#change-timetables>>[init]

# @rt('/timings/delete_timetable_row')
def change_timetable_row(session, idx, new_time, dupli):
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
        # FIXME check first that this is not the last one
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
                Textarea(name="comment", rows=3, placeholder="Enter comment..."),
                Button("Save new gong timing or modify an existing time", type="submit"),
                hx_post="/timings/add_timetable_row",
                hx_target="#center-periods",
            )
        )
    )

# @rt('/timings/add_timetable')
def add_timetable_row(session, period_type, day_type, time, gong_id, auto, targets, comment):
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

# ~/~ end

# ~/~ end
