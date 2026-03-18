# ~/~ begin <<docs/gong-web-app/center-planning.md#libs/planning.py>>[init]
import asyncio
import json
import os
import shutil
from datetime import datetime, timedelta, timezone
from re import match
from urllib.parse import quote_plus
from myFasthtml import *
from libs.utils import display_markdown, feedback_to_user, get_db_path, bypass, Globals, temp_paths
from libs.plancheck import check_plan, get_dhamm_org_types_list, add_end_dates
from libs.dbset import Coming_periods
from libs.utilsJS import JS_BLOCK_NAV, JS_CLIENT_TIMER


# ~/~ begin <<docs/gong-web-app/center-planning.md#create-html-table>>[init]
def show_draft_plan_table(draft_plan, mess):
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
    period_options = [Option(item['period_type'], value=item['period_type']) for item in get_dhamm_org_types_list()]
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
        Div(feedback_to_user(mess), hx_swap_oob="true",id="line-feedback"),
        table,
        form,
        id="planning-periods"
    )

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-planning.md#load-show-center-plan>>[init]
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

def save_db_plan_timetable(center_name, centers):
    source_db_file = get_db_path() + "/" + center_name.lower() + ".ok.db"
    dest_db_file = get_db_path() + "/" + center_name.lower() + ".sending.db"
    if os.path.exists(dest_db_file):
        os.remove(dest_db_file)
    shutil.copy2(Path(source_db_file), Path(dest_db_file))

    dest_db = database(dest_db_file)
    dest_db.execute("DROP TABLE coming_periods")
    #for t in dest_db.t:
    #    dest_db.execute(f"DROP TABLE {str(t)}")
    coming_periods = dest_db.create(Coming_periods, pk='start_date')
    for record in get_plan(temp_paths[center_name]):
        coming_periods.insert(start_date=record["start_date"], period_type=record["period_type"])
    dest_db.close()

    return Path(dest_db_file)

def get_plan(temp_path):
    with open(temp_path, 'r') as f:
        return json.loads(f.read())

def save_plan(temp_path, plan):
    with open(temp_path, "w") as f:
        f.write(json.dumps(plan, default=str))

async def check_save_show_plan(session, plan, centers, mess):
    selected_name = session["center"]
    new_draft_plan = check_plan(session, plan, selected_name, centers)
    await asyncio.to_thread(save_plan, temp_paths[selected_name], new_draft_plan)
    return show_draft_plan_table(new_draft_plan, mess)

# @rt('/planning/delete_line')
async def delete_line(session, centers, index):
    selected_name = session["center"]
    plan = get_plan(temp_paths[selected_name])
    print(f"Deleting line {index} from draft plan with {len(plan)} entries")
    if 0 <= index < len(plan):
        plan.pop(index)
    return await check_save_show_plan(session, plan, centers, {"success": "line_deleted"})

#@rt('/planning/add_line')
async def add_line(session, centers, ptype, start):
    selected_name = session["center"]
    plan = get_plan(temp_paths[selected_name])
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
    plancomp = add_end_dates(plansor, centers[selected_name])
    return await check_save_show_plan(session, plancomp, centers, {"success" : "new_course"})
# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-planning.md#planning-page>>[init]

# @rt('/planning_page')
async def planning_page(session, selected_name, centers, csms, clocks):
    session['planOK'] = False
    center_lock = clocks[selected_name]
    return Main(
        Div(display_markdown("planning-t")),
        Span(
            Span(str(Globals.INITIAL_COUNTDOWN), id="start-time", style="display: none;"),
            Span('/planning/abandon_edit', id="timer-redirect", style="display: none;"),
            Button(f"Modify {selected_name} planning",
                hx_get=f"/planning/load_dhamma_db",
                hx_target="#planning-periods"),
            Span(style="display: inline-block; width: 20px;"),
            Button(f"Modify {selected_name} timetables",
                hx_get="/unfinished?goto_dash=NO",
                hx_target="#planning-periods"),
            Span(style="display: inline-block; width: 20px;"),
            A("return NO CHANGES", href="/planning/abandon_edit", cls="allownavigation"),
            Span(style="display: inline-block; width: 20px;"),
            Span("", id="offset", type="hidden"),
            Button(f"SAVE CHANGES to {selected_name}", id="save-btn",
                hx_get="/save-center-db",
                hx_target="#line-feedback",
                cls="allownavigation") if bypass(session) else None,
            Script("""
            const offset = new Date().getTimezoneOffset();
            const btn = document.getElementById("save-btn"); // <button id="save-btn">
            const current = btn.getAttribute("hx-get");
            const sep = current.includes("?") ? "&" : "?";
            btn.setAttribute("hx-get", current + `${sep}offset=${offset}`);
            //const link = document.getElementById("save-link"); //<a id="save-link">
            //const sep = link.href.includes("?") ? "&" : "?";
            //link.href = link.href + `${sep}offset=${offset}`;
            """),
            Span(style="display: inline-block; width: 20px;"),
            Span("Remainning time: "),
            Span("", id="timer", cls="timer-display")
        ),
        Div(id="line-feedback"),
        Script(JS_CLIENT_TIMER),
        Script(JS_BLOCK_NAV),
        P(""), 
        Div(id="planning-periods"),          # filled by /planning/load_dhamma_db
        cls="container"
    )

#@rt('/status_page')
def status_page(session, center_name, centers, csms, reason, state, err):
    timezon = centers[center_name].timezone
    return Main(
        Div(display_markdown("planning-busy-t")),
        P(f"timezone: {timezon}"),
        P(f"state: {state}"),
        P(f"reason: {reason}"),
        P(f"error: {err}"),
        Ul(*[Li(item) for item in csms[center_name].active_listeners[0].entries]),
        Span(
            A("dashboard", href="/dashboard"),
            Span(style="display: inline-block; width: 20px;"),
            Button("Logout", hx_post="/logout"),
            Span(style="display: inline-block; width: 20px;"),
            A("set FREE",href="/planning/abandon_edit") if bypass(session) else None,        
        ),
        cls="container"
    )


# ~/~ end

# ~/~ end
