# ~/~ begin <<docs/gong-web-app/center-timings.md#libs/timings.py>>[init]

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


# ~/~ begin <<docs/gong-web-app/center-timings.md#check-show-period-types>>[init]

# @rt('/timings/load_center_periods')

def load_timingsubpage(session):
    center = session[utils.Skey.CENTER]
    return Div(
        Div("",hx_swap_oob="true",id="planning-periods"),
        #Div("",hx_swap_oob="true",id="timetables"),
        Div(hx_get= "/timings/center_periods",
            hx_target="#center-periods",
            hx_trigger="load"),
        Div("", id= "center-periods"),
        Div("", id= "periods-struct"),
        Div("", id= "show-times"),
    )

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
        Div("",hx_swap_oob="true",id="periods-struct"),
        Div("",hx_swap_oob="true",id="show-times"),
        H2("Center periods"),
        Div(Safe(html_periods)),
        Div(H3("Timing errors"),
            Safe(html_errors)) if html_errors else None,
    )

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-timings.md#show-struct-timetable>>[init]

# @rt('/timings/select_period')
def select_period(session, period_type, clear_show_times=True):
    center = session[utils.Skey.CENTER]
    periods_struct_df = minio.get_center_temp_df(center, "periods_struct")
    filtered = periods_struct_df[periods_struct_df["period_type"] == period_type]
    filtered["Actions"] = filtered['day_type'].apply(
        lambda dt: A("Select",
            hx_get=f"/timings/select_timetable?period_type={quote_plus(period_type)}&day_type={quote_plus(dt)}",
            hx_target="#show-times"
        )
    )
    html_struct = filtered.to_html(index=False, escape=False)
    return Div(
        Div("",hx_swap_oob="true",id="show-times") if clear_show_times else None,
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
            hx_target="#center-periods"
        )
    )
    filtered = timetables_df[
        (timetables_df["period_type"] == period_type) &
        (timetables_df["day_type"] == day_type)]
    html_timetables = filtered.fillna("").to_html(index=False, escape=False)
    return Div(
        H3(f"Timetable for day type: '{day_type}' in period type: '{period_type}'"),
        Safe(html_timetables)
    )

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-timings.md#delete-timetable-struct>>[init]

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
        show_center_periods(session),
        Div(select_period(session, period_type, clear_show_times=False), 
            hx_swap_oob="true", id="periods-struct"),
        Div(select_timetable(session, period_type, day_type), hx_swap_oob="true", id="show-times")
    )

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-timings.md#load-save-timings>>[init]

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

# ~/~ end

# ~/~ end
