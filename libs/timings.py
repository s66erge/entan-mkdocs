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

def load_timingsubpage(session):
    return Div(
        Div("",hx_swap_oob="true",id="planning-periods"),
        #Div("",hx_swap_oob="true",id="timetables"),
        Div(hx_get= "/timings/center_periods",
            hx_target="#feedback-periods",
            hx_trigger="load"),
        Div("", id= "center-periods"),
        Div("", id= "feedback-periods"),
        Div("", id= "periods-struct"),
        Div("", id= "feedback-times"),
        Div("", id= "show-times"),
        Div("", id= "timetable-form")
    )

def show_center_periods(session):
    center = session[utils.Skey.CENTER]
    session[utils.Skey.TIMESOK] = True
    table = plancheck.get_types_with_duration(center)
    center_periods_df = pd.DataFrame(table)
    minio.save_df_center_temp(center, "center_periods", center_periods_df)
    center_periods_df["Actions"] = center_periods_df['period_type'].apply(
        lambda pt: A("Select",
            hx_get=f"/timings/select_period?period_type={quote_plus(pt)}",
            hx_target="#feedback-times"  # was: periods-struct
        )
    )
    center_periods_df['tags'] = center_periods_df['tags'].map(utils.Globals.HTML_TAGS_CENTERS)
    html_periods = center_periods_df.to_html(index=False, escape=False)
    db = dbset.get_central_db()
    centers = db.create(dbset.Center, pk='center_name')
    center_names = [c.center_name for c in centers()]
    message = {"success": "periods_OK"}
    errors_df = check_timings(session)
    if len(errors_df) > 0:
        session[utils.Skey.TIMESOK] = False
        html_errors = errors_df.to_html(index=False)
        message = {"error": "periods_errors"}
    return Div(
        Div(messages.feedback_to_user(message)),
        Div("",hx_swap_oob="true",id="periods-struct"),
        Div("",hx_swap_oob="true",id="show-times"),
        Div(
            H2("Center periods"),
            Div(Safe(html_periods)),
            Div(
                Form(
                    Span(Label("Select a center to copy a period from:",
                               style="display: inline-block; width: 260px;"),
                        Select(
                            *[Option(c, value=c) for c in center_names],
                            name="center", required=True,
                            style="flex: 0 0 auto; width: 150px;"
                        ),
                    ),
                    Button("Get this center periods", type="submit",
                        style="flex: 0 0 auto; white-space: nowrap; padding: 0.5rem 0.3rem; width: 160px;",
                    ),
                    hx_post=f"/timings/get_other_center_periods",
                    hx_target="#period_form_two",
                    style="display: inline-flex; align-items: center; gap: 0.2rem;"
                ),            
                id="period_form_one"
            ),
            Div("", id="period_form_two"),
            Div(H3("Timing errors"),
                Safe(html_errors)) if len(errors_df) > 0 else None,            
            hx_swap_oob="true", id="center-periods"
        )
    )

def get_other_center_periods(session, center):
    table = plancheck.get_types_with_duration(center)
    periods = [row['period_type'] for row in table if row['tags'] == "F"]
    return Div(
        Form(
            Input(type="hidden", name="from_center", value=center),
            Div(Label("Enter new period name:", style="display: inline-block; width: 180px;"),
                Input(type="text", name="new_period", required=True,
                    style="flex: 0 0 auto; width: 200px;")
            ),
            Span(style="display: inline-block; width: 20px;"),
            Span(Label(f"Select a {center} period to copy from:",
                       style="display: inline-block; width: 260px;"),
                Select(
                    *[Option(p, value=p) for p in periods],
                    name="from_period", required=True,
                    style="flex: 0 0 auto; width: 150px;"
                ),
            ),
            Button("Create new period", type="submit",
                style="flex: 0 0 auto; white-space: nowrap; padding: 0.5rem 0.3rem; width: 160px;",
            ),
            hx_post=f"/timings/create_new_period",
            hx_target="#feedback-times",
            style="display: inline-flex; align-items: center; gap: 0.2rem;"
        ),            
    )


# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-timings.md#show-struct-timetable>>[init]

# @rt('/timings/select_period')
def select_period(session, period_type, clear_show_times=True):
    center = session[utils.Skey.CENTER]
    periods_struct_df = minio.get_center_temp_df(center, "periods_struct")
    timetables_df = minio.get_center_temp_df(center, "timetables")
    day_types = timetables_df[timetables_df["period_type"] == period_type]['day_type'].unique()
    periods_struct_df["Actions"] = periods_struct_df.index.to_series().apply(
        lambda idx: Div(
            A("Detail timings",
                hx_get= ("/timings/select_timings"
                        f"?period_type={quote_plus(period_type)}"
                        f"&day_type={quote_plus(periods_struct_df.at[idx,'day_type'])}"),
                hx_target="#feedback-times"),   # was: show-times 
                Span(style="display: inline-block; width: 50px;"),
            Form(
                Input(type="hidden", name="index", value=idx),
                Select(
                    *[Option(dt, value=dt) for dt in list(day_types)],
                    name="day_type", required=True,
                    style="flex: 0 0 auto; width: 150px;"
                ),
                Button("Select another day type", type="submit",
                    style="flex: 0 0 auto; white-space: nowrap; padding: 0.5rem 0.3rem; width: 200px;",
                ),
                hx_post=f"/timings/modify_day_type",
                hx_target="#center-periods",
                style="display: inline-flex; align-items: center; gap: 0.2rem;"
            ),            
            #style="display: inline-flex; align-items: center; gap: 50px;"
        )
    )
    filtered = periods_struct_df[periods_struct_df["period_type"] == period_type]
    last_idx = filtered.index[-1]
    html_struct = filtered.to_html(index=False, escape=False)
    return Div(
        Div(messages.feedback_to_user({})),
        Div("",hx_swap_oob="true",id="show-times") if clear_show_times else None,
        Div(
            H3(f"Structure for period type: '{period_type}'"),
            Safe(html_struct),
            Span(
                Button(f"Duplicate last day",
                    hx_get=f"/timings/dup_last_day?idx={quote_plus(str(last_idx))}",
                    hx_target="#feedback-times"),
                Span(style="display: inline-block; width: 20px;"),
                Button(f"Delete last day",
                    hx_get=f"/timings/del_last_day?idx={quote_plus(str(last_idx))}",
                    hx_target="#feedback-times"),
                Span(style="display: inline-block; width: 20px;"),
                Button(f"Renumber days from 0",
                    hx_get=f"/timings/renumber_days?period_type={quote_plus(period_type)}",
                    hx_target="#feedback-times"),
                Span(style="display: inline-block; width: 50px;"),
                Form(
                    Input(type="hidden", name="period_type", value=period_type),
                    Div(Label("Enter new day type name:",),
                        Input(type="text", name="new_day_type", required=True,
                            style="flex: 0 0 auto; width: 200px;")
                    ),
                    Span(Label("copied from day type:"),
                        Select(
                            *[Option(dt, value=dt) for dt in list(day_types)],
                            name="day_type", required=True,
                            style="flex: 0 0 auto; width: 150px;"
                        ),
                    ),
                    Button("Create new day type", type="submit",
                        style="flex: 0 0 auto; white-space: nowrap; padding: 0.5rem 0.3rem; width: 160px;",
                    ),
                    hx_post=f"/timings/create_day_type",
                    hx_target="#feedback-times",
                    style="display: inline-flex; align-items: center; gap: 0.2rem;"
                ),            
            ),
            hx_swap_oob="true", id="periods-struct"
        )
    )

# @rt('/timings/select_timings')
def select_timings(session, period_type, day_type):
    center = session[utils.Skey.CENTER]
    timetables_df = minio.get_center_temp_df(center, "timetables")
    timetables_df["Actions"] = timetables_df.index.to_series().apply(
        lambda idx: Div(
            A("Delete",
                hx_get=f"/timings/delete_timetable_row?idx={idx}",
                hx_target="#feedback-times"  # was:center-periods"
            ),
            A("Modify / Add",
                hx_get=f"/timings/load_timing_form?idx={idx}",
                hx_target="#timetable-form"
            ),
            style="display: inline-flex; align-items: center; gap: 25px;"
        )
    )
    filtered = timetables_df[
        (timetables_df["period_type"] == period_type) &
        (timetables_df["day_type"] == day_type)]
    html_timetables = filtered.fillna("").to_html(index=False, escape=False)
    return Div(
        Div(messages.feedback_to_user({})),
        Div(
            H3(f"Timetable for day type: '{day_type}' in period type: '{period_type}'"),
            Safe(html_timetables),
            hx_swap_oob="true", id="show-times"
        )
    )

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-timings.md#load-save-timings>>[init]

def load_timings(center):
    selected_db = dbset.gong_db_name(center)
    db_center = database(utils.get_db_path() + selected_db)
    periods_struct_df = pd.DataFrame(list(db_center.t.periods_struct()))
    minio.save_df_center_temp(center, "periods_struct", periods_struct_df) 
    gongs_df = pd.DataFrame(list(db_center.t.gongs()))
    minio.save_df_center_temp(center, "gongs", gongs_df) 
    targets_df = pd.DataFrame(list(db_center.t.targets()))
    minio.save_df_center_temp(center, "targets", targets_df)
    timetables_df = pd.DataFrame(list(db_center.t.timetables()))
    minio.save_df_center_temp(center, "timetables", timetables_df)
    table = plancheck.get_types_with_duration(center)
    center_periods_df = pd.DataFrame(table)
    minio.save_df_center_temp(center, "center_periods", center_periods_df)
    return

def check_timings(session):
    center = session[utils.Skey.CENTER]
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
