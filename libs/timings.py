# ~/~ begin <<docs/gong-web-app/center-timings.md#libs/timings.py>>[init]

import pandas as pd
from urllib.parse import quote_plus
from fasthtml.common import *
from libs import timechan
import libs.utils as utils
import libs.messages as messages
import libs.plancheck as plancheck
import libs.dbset as dbset
import libs.minio as minio
import libs.timechan as timechan

# ~/~ begin <<docs/gong-web-app/center-timings.md#check-show-period-types>>[init]

# @rt('/timings/load_center_periods')

def load_timingsubpage(request, session):
    params = dict(request.query_params)
    center = session[utils.Skey.CENTER]
    return Div(
        Div("",hx_swap_oob="true",id="planning-periods"),
        #Div("",hx_swap_oob="true",id="timetables"),
        Div(hx_get= "/timings/center_periods",
            hx_target="#center-periods",
            hx_trigger="load"),
        Div("", id= "center-periods"),
        Div("", id= "periods-struct"),
        # Div(messages.feedback_to_user(params), id="feedback-times"),
        Div("", id= "show-times"),
    )

def show_center_periods(session):
    center = session[utils.Skey.CENTER]
    session[utils.Skey.TIMESOK] = True
    center_periods_df = minio.get_center_temp_df(center, "center_periods")
    center_periods_df["Actions"] = center_periods_df['period_type'].apply(
        lambda pt: A("Select",
            hx_get=f"/timings/select_period?period_type={quote_plus(pt)}",
            hx_target="#periods-struct"
        )
    )
    html_periods = center_periods_df.to_html(index=False, escape=False)
    errors_df = check_timings(session)
    if len(errors_df) > 0:
        session[utils.Skey.TIMESOK] = False
        html_errors = errors_df.to_html(index=False)
    return Div(
        Div("",hx_swap_oob="true",id="periods-struct"),
        Div("",hx_swap_oob="true",id="show-times"),
        H2("Center periods"),
        Div(Safe(html_periods)),
        Div(H3("Timing errors"),
            Safe(html_errors)) if len(errors_df) > 0 else H3("No timing errors found"),
    )

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-timings.md#show-struct-timetable>>[init]

# @rt('/timings/select_period')
def select_period(session, period_type, clear_show_times=True):
    center = session[utils.Skey.CENTER]
    periods_struct_df = minio.get_center_temp_df(center, "periods_struct")
    timetables_df = minio.get_center_temp_df(center, "timetables")
    day_types = timetables_df[timetables_df["period_type"] == period_type]['day_type'].unique()
    print(list(day_types))
    filtered = periods_struct_df[periods_struct_df["period_type"] == period_type]
    filtered["Actions"] = filtered.index.to_series().apply(
        lambda idx: Div(
            A("Detail timings",
                hx_get=f"/timings/select_timetable?period_type={quote_plus(period_type)}&day_type={quote_plus(filtered.at[idx,"day_type"])}",
                hx_target="#show-times"
            ),
            Form(
                Input(type="hidden", name="index", value=idx),
                Input(list="day_type", name="day_type", required=True,
                        style="flex: 0 0 auto; width: 250px;"),
                Datalist(
                    *[Option(dt, value=dt) for dt in list(day_types)],
                    id="day_type",
                ),
                # FIXME replace with "Choose day_type or create new one" when ready
                Button("--- NOT WORKING ---", type="submit",
                    style="flex: 0 0 auto; white-space: nowrap; padding: 0.5rem 0.3rem; width: 260px;",
                ),
                hx_post=f"/timings/change_day_type",
                hx_target="#center-periods",
                style="display: inline-flex; align-items: center; gap: 0.2rem;"
            ),            
            style="display: inline-flex; align-items: center; gap: 50px;"
        )
    )
    html_struct = filtered.to_html(index=False, escape=False)
    return Div(
        Div("",hx_swap_oob="true",id="show-times") if clear_show_times else None,
        H3(f"Structure for period type: '{period_type}'"),
        Safe(html_struct),
    )

# @rt('/timings/select_timetable')
def select_timetable(session, params, period_type, day_type):
    center = session[utils.Skey.CENTER]
    timetables_df = minio.get_center_temp_df(center, "timetables")
    timetables_df["Actions"] = timetables_df.index.to_series().apply(
        lambda idx: Div(
            A("Delete",
                hx_get=f"/timings/delete_timetable_row?idx={idx}",
                hx_target="#center-periods"
            ),
            Form(
                Input(type="hidden", name="index", value=idx),
                Input(type="time", name="new_time", required=True, 
                    style="flex: 0 0 auto; width: 100px;"),
                Button("Duplicate", type="submit", 
                    style="flex: 0 0 auto; white-space: nowrap; padding: 0.5rem 0.3rem; width: 80px;"),
                hx_post=f"/timings/duplicate_timetable_row",
                hx_target="#center-periods",
                style="display: inline-flex; align-items: center; gap: 0.2rem;"
            ),            
            style="display: inline-flex; align-items: center; gap: 25px;"
        )
    )
    filtered = timetables_df[
        (timetables_df["period_type"] == period_type) &
        (timetables_df["day_type"] == day_type)]
    html_timetables = filtered.fillna("").to_html(index=False, escape=False)
    return Div(
        H3(f"Timetable for day type: '{day_type}' in period type: '{period_type}'"),
        Div(messages.feedback_to_user(params), id="feedback-times"),
        Safe(html_timetables),
        timechan.timetable_form(session, period_type, day_type)
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
    session[utils.Skey.SAVED_TIMES] = True
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
        periods_struct_df.groupby("period_type")["day"].apply(set).to_dict())
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

    duplicated_times = timetables_df[timetables_df.duplicated(
        subset=["period_type", "day_type", "time"], keep=False)]
    duplicated_times = duplicated_times[["period_type", "day_type", "time"]]
    duplicated_times["error"] = "Duplicated time"

    valid_targets = set(targets_df["shortname"])
    invalid_targets = timetables_df.loc[
        ~timetables_df["targets"].str.split().apply(lambda t: set(t).issubset(valid_targets)),
        ["period_type", "day_type", "time", "targets"]
    ]
    invalid_targets["error"] = "At least one invalid target"

    errors_df = pd.concat([errors_df, invalid_day_types, duplicated_times, invalid_gongs,invalid_targets], ignore_index=True)
    errors2_df = errors_df.fillna("")
    errors2_df["gong_id"] = errors2_df["gong_id"].apply(
        lambda x: int(x) if isinstance(x, float) and pd.notna(x) else ""
    )
    return errors2_df

# ~/~ end

# ~/~ end
