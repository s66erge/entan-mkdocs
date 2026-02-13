# ~/~ begin <<docs/gong-web-app/center-planning.md#libs/planning.py>>[init]
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from asyncio import sleep
from urllib.parse import quote_plus
from tabulate import tabulate
from fasthtml.common import *

from libs.utils import display_markdown, isa_dev_computer, feedback_to_user, Globals
from libs.fetch import fetch_dhamma_courses, check_plan
from libs.utilsJS import JS_BLOCK_NAV

# ~/~ begin <<docs/gong-web-app/center-planning.md#abandon-edit>>[init]

# @rt('/planning/abandon_edit')
def abandon_edit(session, csms):
    this_center = session["center"]
    session["center"] = ""
    if this_center and csms[this_center].current_state.id == "edit":
        csms[this_center].model.user = None
        csms[this_center].send("abandon_changes")
    return Redirect('/dashboard')

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-planning.md#js-client-timer>>[init]

JS_CLIENT_TIMER = """
function startCountdown(seconds, elementId) {
    const element = document.getElementById(elementId);
    let timeLeft = seconds;

    function updateDisplay() {
        if (timeLeft > 60) {
            const minutes = Math.floor(timeLeft / 60);
            element.textContent = `${minutes} min`;
        } else {
            element.textContent = `${timeLeft} sec`;
        }
    }
    updateDisplay();

    const interval = setInterval(() => {
        timeLeft--;
        updateDisplay();    
        if (timeLeft <= 0) {
            clearInterval(interval);
            window.onbeforeunload = null;
            window.location.href = '/planning/abandon_edit';
        }
    }, 1000);
}
// Get starting time from #start-time element and START AUTOMATICALLY
const startSeconds = parseInt(document.getElementById('start-time').textContent);
startCountdown(startSeconds, 'timer');

"""
# ~/~ end
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
        check_cell = Td(check, style="background: red") if not check.startswith("OK") else Td(check)
        source_cell = Td(source, style="background: blue") if source == "new input" else Td(source)
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
    form = Form(
        Div(
            Label("Period type:"),
            Input(type="text", name="ptype", placeholder="e.g. '10 days'", style="width: 200px"),
            Label("Start date:"),
            Input(type="date", name="start", value=today.strftime('%Y-%m-%d'), style="width: 200px"),
            Label("End date:"),
            Input(type="date", name="end", value=(today+timedelta(days=10)).strftime('%Y-%m-%d'), style="width: 200px"),
            Button("Add Period", type="submit")
        ),
        hx_post="/planning/add_line",
        hx_target="#planning-periods",
        ),

    table = Table(
        Thead( Tr( Th("Start date"), Th("End date"), Th("Period type"), Th("Source"), Th("Check"), Th("Info given by center in dhamma.org"), Th("Action"),)),
        Tbody(*rows)
    )
    print(mess)
    return Div(
        H2("Plan with 'www.google.org' added for 12 months from current course start"),
        table,
        Div(feedback_to_user(mess), id="line-feedback"),
        form,
        id="planning-periods"
    )

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-planning.md#load-show-center-plan>>[init]

# @rt('/planning/load_dhamma_db')
def load_dhamma_db(session):
    return Div(
        P(" Loading this center planning from dhamma.org ..."),
        Div(hx_get=f"/planning/show_dhamma", 
            hx_target="#planning-periods",
            hx_trigger="load",  # Triggers when this div loads
            style="display: none;"),
        id="planning-periods"
    )

# @rt('/planning/show_dhamma')
def show_dhamma(session, plan, db, mess):
    selected_name = session["center"]
    if plan == []:
        merged_plan = fetch_dhamma_courses(selected_name, 12, 0)
    else:
        merged_plan = plan
    new_draft_plan = check_plan(merged_plan, selected_name, db)
    # print(tabulate(new_draft_plan, headers="keys", tablefmt="grid"))
    # Save to db for future modifications
    centers = db.t.centers
    centers.update(center_name=selected_name, json_save=json.dumps(new_draft_plan, default=str))
    return show_draft_plan_table(new_draft_plan, mess)

# @rt('/planning/delete_line')
def delete_line(session, db, index: int):
    selected_name = session["center"]
    centers = db.t.centers
    Center = centers.dataclass()
    plan = json.loads(centers[selected_name].json_save)
    print(f"Deleting line {index} from draft plan with {len(plan)} entries")
    if 0 <= index < len(plan):
        plan.pop(index)
    return show_dhamma(session, plan, db, {"success": "line_deleted"})

def add_line(session, db, ptype, start, end):
    selected_name = session["center"]
    centers = db.t.centers
    Center = centers.dataclass()
    plan = json.loads(centers[selected_name].json_save)
    # Create new plan line with user input
    new_line = {
        "start_date": start,
        "end_date": end,
        "period_type": ptype,
        "source": "new input",
        "check": "",
        "course_type": ""
    }    
    # Add the new line to the plan
    plan.append(new_line)    
    # Sort plan by start_date
    plansor = sorted(plan, key=lambda x: x["start_date"])
    return show_dhamma(session, plansor, db, {"success" : "new_course"})

# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-planning.md#planning-page>>[init]

# @rt('/planning_page')
def planning_page(session, selected_name, db, csms):
    session["center"] = selected_name
    state_mach = csms[selected_name]
    this_user= session['auth']
    # FIXME use SQL db commit for the following 5 lines 
    start_state_time = state_mach.model.get_start_time()
    past = datetime.fromisoformat(start_state_time.replace("Z", "+00:00"))
    tnow = datetime.now(timezone.utc)
    delta = (tnow-past).total_seconds()
    # print(f"state start: {start_state_time}, now: {tnow.strftime('%Y-%m-%dT%H:%M:%S+00:00')}, delta: {delta}")
    if state_mach.current_state.id == "edit" and (
        delta > Globals.INITIAL_COUNTDOWN or this_user == state_mach.model.get_user()):
        state_mach.send("abandon_changes")
    if state_mach.current_state.id == "free":
        state_mach.model.user = this_user
        state_mach.send("starts_editing")
        print(session)
        return Main(
            Div(display_markdown("planning-t")),
            Span(
                Span(str(Globals.INITIAL_COUNTDOWN), id="start-time", style="display: none;"),
                Button(f"Modify {selected_name} planning",
                    hx_get=f"/planning/load_dhamma_db?selected_name={quote_plus(selected_name)}",
                    hx_target="#planning-periods"),
                Span(style="display: inline-block; width: 20px;"),
                Button(f"Modify {selected_name} course types / timetables",
                    hx_get="/unfinished?goto_dash=NO",
                    hx_target="#planning-periods"),
                Span(style="display: inline-block; width: 20px;"),
                A("return NO CHANGES",href="/planning/abandon_edit", _data_safe_nav="true"),
                Span(style="display: inline-block; width: 20px;"),
                Span("Remainning time: "),
                Span("", id="timer", cls="timer-display")
            ),
            Script(JS_CLIENT_TIMER),
            Script(JS_BLOCK_NAV),
            P(""), 
            Div(id="planning-periods"),          # filled by /planning/load_dhamma_db
            cls="container"
        )
    else: 
        centers = db.t.centers
        Center = centers.dataclass()
        timezon = centers[selected_name].timezone
        return Main(
            P(f"Anoher user has initiated a session to modify this center gong planning. To bring new changes, you must wait until the modified planning has been installed into the local center computer. This will happen at 3am, local time of the center: {timezon}"),
            P("If you want to consult any center in the mean time, go to the dashboard. Otherwise please logout."),
            Span(
                A("dashboard", href="/dashboard"),
                Span(style="display: inline-block; width: 20px;"),
                Button("Logout", hx_post="/logout"),
                Span(style="display: inline-block; width: 20px;"),
                A("set FREE",href="/planning/abandon_edit") if isa_dev_computer() else None,        
            ),
            cls="container"
        )

# ~/~ end

# ~/~ end
