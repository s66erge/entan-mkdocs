# ~/~ begin <<docs/gong-web-app/gong-planning.md#libs/planning.py>>[init]

import asyncio
import os
import shutil
import pandas as pd
from datetime import datetime
from fasthtml.common import *
import libs.utils as utils
import libs.messages as messages
import libs.plancheck as plancheck
import libs.fetch as fetch
import libs.dbset as dbset
import libs.minio as minio
import libs.utilsJS as utilsJS

# ~/~ begin <<docs/gong-web-app/gong-planning.md#create-html-table>>[init]

def show_draft_plan_table(draft_plan, center, mess):
    # Create an HTML table from a draft plan list of dictionaries
    rows = []
    for idx, plan_line in enumerate(sorted(draft_plan, key=lambda x: getattr(x, "start_date", ""))):
        start = plan_line.get("start_date")
        end = plan_line.get("end_date")
        ptype = plan_line.get("period_type")
        source = plan_line.get("source")
        check = plan_line.get("check")
        course = plan_line.get("course_type")
        no_gong = plan_line.get("No_gong", "")
        # Conditional coloring
        ptype_cell = Td(B(ptype), style="color: white; background: red") if ptype.startswith("UNKNOWN") else Td(B(ptype))
        source_cell = Td(source, style="color: white; background: blue") if source in "new input-fill gap" else Td(source)
        match check[0:2]:
            case "OK":
                check_cell = Td(check)
            case "CH":
                check_cell = Td(check, style="color: black; background: darkorange")
            case _:
                check_cell = Td(check, style="color: white; background: red")
        # Add delete link for removing this row
        delete_link = A("Delete",
            hx_post=f"/planning/delete_line/{idx}",
            hx_target="#planning-periods",
            hx_confirm="Are you sure you want to delete this entry?",
        )
        rows.append(
            Tr(
                Td(B(start)), ptype_cell, Td(end), source_cell, check_cell, Td(course), Td(no_gong), Td(delete_link)
            )
        )
    today = datetime.now().date()
    period_types_in_db = plancheck.get_period_types_list(center)
    period_options = [Option(item, value=item) for item in sorted(list(period_types_in_db))]
    form = Form(
        Div(
            Label("Period type:"),
            Select(
                Option("", value="", selected=True, disabled=True, text="Select period type..."),
                *period_options,
                name="ptype",
                style="width: 200px"
            ),
            Label("Start date:"),
            #Input(type="date", name="start", value=today.strftime('%Y-%m-%d'), style="width: 200px"),
            Input(id="date", name="start"),
            Script(f"""
                   flatpickr("#date", {{
                        dateFormat: "Y-m-d",
                        altInput: true,
                        altFormat: "Y-m-d",
                        locale: {{ firstDayOfWeek: 1 }},
                        defaultDate: "{today}"
                    }});
                   """),
            Button("Add Period", type="submit")
        ),
        hx_post="/planning/add_line",
        hx_target="#planning-periods",
        ),
    table = Table(
        Thead( Tr( Th("Start date"), Th("Period type"), Th("End date"), Th("Source"), Th("Check"), Th("Info given by center in dhamma.org"), Th("No_gong"), Th("Action"),)),
        Tbody(*rows)
    )
    return Div(
        H2("Current plan with 'www.dhamma.org' added for 12 months from current course start"),
        Div(messages.feedback_to_user(mess), hx_swap_oob="true",id="line-feedback"),
        Div("",hx_swap_oob="true",id="timingsubpage"),
        utils.toggle_markdown("current-plan-instructions"),
        table,
        form,
        id="planning-periods"
    )

# ~/~ end
# ~/~ begin <<docs/gong-web-app/gong-planning.md#load-show-center-plan>>[init]

# @rt('/planning/load_dhamma_db')
def load_dhamma_db(session):
    return Div(
        Div("", hx_swap_oob="true", id="timingsubpage"),
        Div(
            P(" Loading this center planning from dhamma.org ..."),
            Div(hx_get="/planning/check_show_dhamma", 
                hx_target="#planning-periods",
                hx_trigger="load",  # Triggers when this div loads
                style="display: none;"),
            id="planning-periods"
        )
    )

def replace_table(conn, name, df):
    df.to_sql(name, conn, if_exists="replace", index=False)

async def save_db_plan_timetable(center_name):
    source_db_file = utils.get_db_path() + dbset.gong_db_name(center_name)
    filename = dbset.gong_db_name(center_name, utils.Globals.SENDING)
    dest_db_file = utils.get_db_path() + filename
    if os.path.exists(dest_db_file):
        os.remove(dest_db_file)
    await asyncio.to_thread(shutil.copy2, Path(source_db_file), Path(dest_db_file))

    dest_db = database(dest_db_file)
    #for t in dest_db.t:
    #    dest_db.execute(f"DROP TABLE {str(t)}")
    dest_db.execute("DROP TABLE coming_periods")
    coming_periods = dest_db.create(dbset.Coming_periods, pk='start_date')
    for record in minio.get_center_temp_list_of_dicts(center_name, "planning"):
        coming_periods.insert(start_date=record["start_date"], period_type=record["period_type"])

    dest_db.execute("DROP TABLE periods_struct")
    periods_struct = dest_db.create(dbset.Periods_struct, pk=('period_type', 'day'))
    for record in minio.get_center_temp_list_of_dicts(center_name, "periods_struct"):
        periods_struct.insert(period_type=record["period_type"], day=record["day"],
                              day_type=record["day_type"])

    dest_db.execute("DROP TABLE timetables")
    timetables = dest_db.create(dbset.Timetables, pk=('period_type', 'day_type', 'time'))
    for record in minio.get_center_temp_list_of_dicts(center_name, "timetables"):
        timetables.insert(period_type=record["period_type"], day_type=record["day_type"],
                          time=record["time"], gong_id=record["gong_id"], auto=record["auto"],
                          targets=record["targets"], comment=record["comment"])
    dest_db.close()

    return filename

async def check_save_show_plan(session, start_plan, mess):
    selected_name = session[utils.Skey.CENTER]
    inside = minio.dicts_from_excel_minio(selected_name,"inside")
    plan = fetch.sort_clean(selected_name,start_plan, inside)
    new_draft_plan = plancheck.check_plan(session, plan, selected_name)
    if not session[utils.Skey.PLANOK]:
        mess_after_check = {"error":"plan_not_ok"}
    else:
        mess_after_check = mess
    await asyncio.to_thread(minio.save_center_temp_list_of_dicts, selected_name, "planning", new_draft_plan)
    session[utils.Skey.SAVED_PLAN] = True
    return show_draft_plan_table(new_draft_plan, selected_name, mess_after_check)

# @rt('/planning/delete_line')
async def delete_line(session, index):
    selected_name = session[utils.Skey.CENTER]
    plan = minio.get_center_temp_list_of_dicts(selected_name, "planning")
    print(f"Deleting line {index} from draft plan with {len(plan)} entries")
    if 0 <= index < len(plan):
        plan.pop(index)
    return await check_save_show_plan(session, plan, {"success": "line_deleted"})

#@rt('/planning/add_line')
async def add_line(session, ptype, start):
    selected_name = session[utils.Skey.CENTER]
    plan = minio.get_center_temp_list_of_dicts(selected_name, "planning")
    # Create new plan line with user input
    new_line = {
        "start_date": start,
        "period_type": ptype,
        "source": "new input",
        "check": "",
        "course_type": "",
        "No_gong": ""
    }    
    # Add the new line to the plan
    plan.append(new_line)
    # Sort plan by start_date
    plansor = sorted(plan, key=lambda x: x['start_date'])
    plancomp = plancheck.add_end_dates(plansor, selected_name)
    return await check_save_show_plan(session, plancomp, {"success" : "new_course"})
# ~/~ end
# ~/~ begin <<docs/gong-web-app/gong-planning.md#planning-page>>[init]

def load_minio_timings_from_db(center):
    selected_db = dbset.gong_db_name(center)
    db_center = database(utils.get_db_path() + selected_db)
    periods_struct_df = pd.DataFrame(list(db_center.t.periods_struct()))
    minio.save_df_center_temp(center, "periods_struct", periods_struct_df) 
    timetables_df = pd.DataFrame(list(db_center.t.timetables()))
    minio.save_df_center_temp(center, "timetables", timetables_df)
    db_center.close()
    return

# @rt('/planning_page')
async def planning_page(session, selected_name, csms):
    load_minio_timings_from_db(selected_name)
    return Main(
        H1(f"Change {selected_name} planning and/or timetables"),
        utils.toggle_markdown("how-to-save-your-work"),
        Div("",style="height: 4px;"),  # spacer
        utils.toggle_markdown("planning-menu-below"),
        Br(),
        Span(
            Span(str(utils.Globals.INITIAL_COUNTDOWN), id="start-time", style="display: none;"),
            Span('/planning/timer_done', id="timer-redirect", style="display: none;"),
            Button("(re)Start getting plans",
                hx_get="/planning/load_dhamma_db",
                hx_target="#planning-periods"),
            Span(style="display: inline-block; width: 20px;"),
            Button("Load saved plan",
                hx_get="/planning/saved_plan",
                hx_target="#planning-periods"),
            Span(style="display: inline-block; width: 20px;"),
            Button("(re)Start timetables",
                hx_get=f"/timings/timingsubpage?center={selected_name}",
                hx_target="#timingsubpage"),
            Span(style="display: inline-block; width: 20px;"),
            Button("Load saved timetables",
                hx_get="/timings/saved_timings",
                hx_target="#timingsubpage"),
            Span(style="display: inline-block; width: 20px;"),
            A("return NO CHANGES", id="abandon", href="/planning/abandon_edit", cls="allownavigation"),
            Span(style="display: inline-block; width: 20px;"),
            Button("SAVE ALL CHANGES", id="save-btn",
                hx_get="/save-center-db",
                hx_target="#line-feedback",
                hx_confirm=("Are you ABSOLUTELY sure you want to save your work now? "
                        "It will then be sent to the center by 2 a.m. center local time"),
                hx_on_click="""
                    document.getElementById('end-link').classList.remove('hidden');
                    document.getElementById('abandon').classList.add('hidden');
                    document.getElementById('save-btn').classList.add('hidden');
                """,
                cls="allownavigation"
                ),
            Span(style="display: inline-block; width: 20px;"),
            A("return to STATUS after SAVING ALL CHANGES", id="end-link",
              href=f"/status_page?center={selected_name}", cls="allownavigation hidden")
        ),
        Br(), Br(),
        Span(
            Button("Download PDF", onclick="window.print()"),
            Span(style="display: inline-block; width: 20px;"),
            A("open this center status tab", href=f"/status_page?center={selected_name}", target="_blank", cls="allownavigation"),
            Span(style="display: inline-block; width: 20px;"),
            A("open all centers consult tab", href="/consult_page", target="_blank", cls="allownavigation"),
            Span(style="display: inline-block; width: 20px;"),
            Span("Remainning time: "),
            Span("", id="timer", cls="timer-display")
        ),
        Div(id="line-feedback"),
        Script(utilsJS.JS_CLIENT_TIMER),
        Script(utilsJS.JS_BLOCK_NAV),
        P(""), 
        Div(id="planning-periods"),    # filled by /planning/load_dhamma_db
        Div(id="timingsubpage"),       # filled by /timings/timingsubpage      
        cls="container"
    )

# ~/~ end

# ~/~ end
