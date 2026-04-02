# Center planning page

Will only be reachable for authenticated users and planner for the selected center.

```python
#| file: libs/planning.py 

import asyncio
import json
import os
import shutil
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

<<create-html-table>>
<<load-show-center-plan>>
<<planning-page>>

```

### Planning page

Check first if the center is available for edits, either:

-  if state is "edit" and the state changes happenned more than 'max time' ago, then force it to 'free' first
-  state is "free"

Then:

- available: load the main menu for changing center planning
- not available: explain to the user to wait for current changes to enter production at center 

```python
#| id: planning-page

# @rt('/planning_page')
async def planning_page(session, selected_name, centers, csms):
    session['planOK'] = False
    return Main(
        Div(utils.display_markdown("planning-t", selected_name)),
        Span(
            Span(str(utils.Globals.INITIAL_COUNTDOWN), id="start-time", style="display: none;"),
            Span('/planning/timer_done', id="timer-redirect", style="display: none;"),
            Button(f"(re)Start planning",
                hx_get=f"/planning/load_dhamma_db",
                hx_target="#planning-periods"),
            Span(style="display: inline-block; width: 20px;"),
            Button(f"Load saved plan",
                hx_get=f"/planning/saved_plan",
                hx_target="#planning-periods"),
            Span(style="display: inline-block; width: 20px;"),
            Button(f"(re)Start timetables",
                hx_get="/unfinished?goto_dash=NO",
                hx_target="#planning-periods"),
            Span(style="display: inline-block; width: 20px;"),
            Button(f"Load saved timetables",
                hx_get="/unfinished?goto_dash=NO",
                hx_target="#planning-periods"),
            Span(style="display: inline-block; width: 20px;"),
            A("return NO CHANGES", href="/planning/abandon_edit", cls="allownavigation"),
            Span(style="display: inline-block; width: 20px;"),
            Span("", id="offset", type="hidden"),
            Button(f"SAVE ALL CHANGES", id="save-btn",
                hx_get="/save-center-db",
                hx_target="#line-feedback",
                cls="allownavigation") if utils.dev_comp_or_user(session) else None,
            Span(style="display: inline-block; width: 20px;"),
            Span("Remainning time: "),
            Span("", id="timer", cls="timer-display")
        ),
        Div(id="line-feedback"),
        Script(utilsJS.JS_CLIENT_TIMER),
        Script(utilsJS.JS_BLOCK_NAV),
        P(""), 
        Div(id="planning-periods"),          # filled by /planning/load_dhamma_db
        cls="container"
    )

```

### Create colored html table of current plan

```python
#| id: create-html-table

def show_draft_plan_table(draft_plan, center_obj, mess):
    # Create an HTML table from a draft plan list of dictionaries
    rows = []
    for idx, plan_line in enumerate(sorted(draft_plan, key=lambda x: getattr(x, "start_date", ""))):
        start = plan_line.get("start_date")
        end = plan_line.get("end_date")
        ptype = plan_line.get("period_type")
        source = plan_line.get("source")
        check = plan_line.get("check")
        course = plan_line.get("course_type")
        # Conditional coloring
        ptype_cell = Td(ptype, style="background: red") if ptype.startswith("UNKNOWN") else Td(ptype)
        source_cell = Td(source, style="background: blue") if source == "new input" else Td(source)
        match check[0:2]:
            case "OK":
                check_cell = Td(check)
            case "CH":
                check_cell = Td(check, style="background: orange")
            case _:
                check_cell = Td(check, style="background: red")
        # Add delete link for removing this row
        delete_link = A("Delete",
            hx_post=f"/planning/delete_line/{idx}",
            hx_target="#planning-periods",
            hx_confirm="Are you sure you want to delete this entry?",
        )
        rows.append(
            Tr(
                Td(start), Td(end), ptype_cell, source_cell, check_cell, Td(course), Td(delete_link)
            )
        )

    today = datetime.now().date()
    _, period_types_in_db = plancheck.get_period_types_in_db(center_obj)
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
            Input(type="date", name="start", value=today.strftime('%Y-%m-%d'), style="width: 200px"),
            Button("Add Period", type="submit")
        ),
        hx_post="/planning/add_line",
        hx_target="#planning-periods",
        ),

    table = Table(
        Thead( Tr( Th("Start date"), Th("End date"), Th("Period type"), Th("Source"), Th("Check"), Th("Info given by center in dhamma.org"), Th("Action"),)),
        Tbody(*rows)
    )
    return Div(
        H2("Plan with 'www.google.org' added for 12 months from current course start"),
        Div(utils.feedback_to_user(mess), hx_swap_oob="true",id="line-feedback"),
        table,
        form,
        id="planning-periods"
    )

```

### Load from dhamma.org and show the merged and checked center plan

```python
#| id: load-show-center-plan
# @rt('/planning/load_dhamma_db')
def load_dhamma_db(session):
    return Div(
        P(" Loading this center planning from dhamma.org ..."),
        Div(hx_get=f"/planning/check_show_dhamma", 
            hx_target="#planning-periods",
            hx_trigger="load",  # Triggers when this div loads
            style="display: none;"),
        id="planning-periods"
    )

async def save_db_plan_timetable(center_name, centers):
    source_db_file = utils.get_db_path() + dbset.gong_db_name(center_name)
    filename = dbset.gong_db_name(center_name, "sending")
    dest_db_file = utils.get_db_path() + filename
    if os.path.exists(dest_db_file):
        os.remove(dest_db_file)
    await asyncio.to_thread(shutil.copy2, Path(source_db_file), Path(dest_db_file))

    dest_db = database(dest_db_file)
    dest_db.execute("DROP TABLE coming_periods")
    #for t in dest_db.t:
    #    dest_db.execute(f"DROP TABLE {str(t)}")
    coming_periods = dest_db.create(dbset.Coming_periods, pk='start_date')
    for record in minio.get_center_temp_data(center_name, "planning"):
        coming_periods.insert(start_date=record["start_date"], period_type=record["period_type"])
    dest_db.close()
    return filename

async def check_save_show_plan(session, start_plan, centers, mess):
    selected_name = session[utils.Skey.CENTER]
    inside = minio.dicts_from_excel_minio(selected_name,"inside")
    dhamma_types = minio.dicts_from_excel_minio("all_centers", "dhamma_course")

    plan = fetch.sort_clean(start_plan, dhamma_types, inside)

    new_draft_plan = plancheck.check_plan(session, plan, selected_name, centers)
    await asyncio.to_thread(minio.save_center_temp_data, selected_name, "planning", new_draft_plan)
    return show_draft_plan_table(new_draft_plan, centers[selected_name], mess)

# @rt('/planning/delete_line')
async def delete_line(session, centers, index):
    selected_name = session[utils.Skey.CENTER]
    plan = minio.get_center_temp_data(selected_name, "planning")
    print(f"Deleting line {index} from draft plan with {len(plan)} entries")
    if 0 <= index < len(plan):
        plan.pop(index)
    return await check_save_show_plan(session, plan, centers, {"success": "line_deleted"})

#@rt('/planning/add_line')
async def add_line(session, centers, ptype, start):
    selected_name = session[utils.Skey.CENTER]
    plan = minio.get_center_temp_data(selected_name, "planning")
    # Create new plan line with user input
    new_line = {
        "start_date": start,
        "period_type": ptype,
        "source": "new input",
        "check": "",
        "course_type": ""
    }    
    # Add the new line to the plan
    plan.append(new_line)    
    # Sort plan by start_date
    plansor = sorted(plan, key=lambda x: x['start_date'])
    plancomp = plancheck.add_end_dates(plansor, centers[selected_name])
    return await check_save_show_plan(session, plancomp, centers, {"success" : "new_course"})
```
