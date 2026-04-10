# ~/~ begin <<docs/gong-web-app/center-timings.md#libs/timings.py>>[init]

import asyncio
import json
import os
import shutil
import pandas as pd
from tabulate import tabulate
from datetime import datetime
from zoneinfo import ZoneInfo
from fasthtml.common import *
import libs.utils as utils
import libs.cdash as cdash 
import libs.plancheck as plancheck
import libs.fetch as fetch
import libs.dbset as dbset
import libs.minio as minio
import libs.utilsJS as utilsJS

# ~/~ begin <<docs/gong-web-app/center-timings.md#load-show-timetables>>[init]

# @rt('/timings/load_center_periods')
def show_center_periods(session):
    center = session[utils.Skey.CENTER]
    center_periods_df = minio.get_center_temp_df(center, "center_periods")
    html_periods = center_periods_df.to_html(index=False)
    errors_df = check_timetables(session)
    html_errors = errors_df.to_html(index=False) if not errors_df.empty else None
    return Div(
        H2("Center periods"),
        Div("",hx_swap_oob="true",id="planning-periods"),
        Div(Safe(html_periods)),
        Div(Safe(html_errors)) if html_errors else None,
    )

def load_periods_timetables(session):
    center = session[utils.Skey.CENTER]
    selected_db = dbset.gong_db_name(center)
    table = plancheck.get_types_with_duration(center)
    center_periods_df = pd.DataFrame(table)
    center_periods_df['check'] = "OK"
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

def check_timetables(session):
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
# ~/~ begin <<docs/gong-web-app/center-timings.md#create-periods-table>>[init]

def something():
    return None

# ~/~ end

# ~/~ end
