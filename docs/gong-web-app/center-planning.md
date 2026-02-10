# Center consult page

Will only be reachable for authenticated users.

```{.python file=libs/planning.py}
import json
from datetime import datetime, timezone
from pathlib import Path
from asyncio import sleep
from urllib.parse import quote_plus
from tabulate import tabulate
from fasthtml.common import *

from libs.utils import display_markdown, isa_dev_computer, Globals
from libs.fetch import fetch_dhamma_courses, check_plan
from libs.dbset import get_central_db


<<planning-page>>
```


### Planning page

```{.python #planning-page}

def abandon_edit(session, csms):
    this_center = session["center"]
    session["center"] = ""
    csms[this_center].model.user = None
    csms[this_center].send("abandon_changes")
    return RedirectResponse('/dashboard')

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
                A("return NO CHANGES",href="/planning/abandon_edit",),
                Span(style="display: inline-block; width: 20px;"),
                Span("Remainning time: "),
                Span("", id="timer", cls="timer-display")
            ),
            Script("""
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
                        window.location.href = '/planning/abandon_edit';
                    }
                }, 1000);
                }
                // Get starting time from #start-time element and START AUTOMATICALLY
                const startSeconds = parseInt(document.getElementById('start-time').textContent);
                startCountdown(startSeconds, 'timer');            
                """
            ),

            P(""),       
            Div(id="planning-periods"),          # filled by /planning/load_dhamma_db
            cls="container"
        )
    else: 
        centers = db.t.centers
        Center = centers.dataclass()
        timezon = centers[selected_name].timezone
        return Div(
            P(f"Anoher user has initiated a session to modify this center gong planning. To bring new changes, you must wait until the modified planning has been installed into the local center computer. This will happen at 3am, local time of the center: {timezon}"),
            P("If you want to consult any center in the mean time, go to the dashboard. Otherwise please logout."),
            Span(
                A("dashboard", href="/dashboard"),
                Span(style="display: inline-block; width: 20px;"),
                Button("Logout", hx_post="/logout"),
                Span(style="display: inline-block; width: 20px;"),
                A("set FREE",href="/planning/abandon_edit") if isa_dev_computer() else None,        
            )
        )


def create_draft_plan_table(draft_plan):
    # Create an HTML table from a draft plan list of  dictionaries
    rows = []
    for plan_line in sorted(draft_plan, key=lambda x: getattr(x, "start_date", "")):
        start = plan_line.get("start_date")
        end = plan_line.get("end_date")
        ptype = plan_line.get("period_type")
        source = plan_line.get("source")
        check = plan_line.get("check")
        course = plan_line.get("course_type")
        # Color period_type red if it's starting with UNKNOWN
        if ptype.startswith("UNKNOWN"):
            ptype_cell = Td(ptype, style="background: red")
        else:
            ptype_cell = Td(ptype)
        if not check.startswith("OK"):
            check_cell = Td(check, style="background: red")
        else:
            check_cell = Td(check)
        rows.append(Tr(Td(start), Td(end), ptype_cell, Td(source), check_cell, Td(course)))

    table = Table(
        Thead(Tr(Th("Start date"), Th("End date"), Th("Period type"), Th("source"), Th("check"),
        Th("Dhamma.org center course"))),
        Tbody(*rows)
    )
    return table

# @rt('/planning/load_dhamma_db')
def load_dhamma_db(session):
    this_center = session["center"]
    return Div(
        P(" Loading from dhamma.org ..."),
        Div(hx_get=f"/planning/show_dhamma?selected_name={quote_plus(this_center)}", 
            hx_target="#planning-periods",
            hx_trigger="load",  # Triggers when this div loads
            style="display: none;"),
        id="planning-periods"
    )

# @rt('/planning/show_dhamma')
def show_dhamma(session, request, db, db_path):
    centers = db.t.centers
    selected_name = session["center"]
    Center = centers.dataclass()
    selected_db = centers[selected_name].gong_db_name
    dbfile_path = Path(db_path) / selected_db
    if not dbfile_path.exists():
        return Div(P(f"Database not found: {selected_db}"))
    db_center = database(str(dbfile_path))
    other_course = json.loads(centers[selected_name].other_course)
    new_merged_plan = fetch_dhamma_courses(selected_name, 12, 0)
    new_draft_plan = check_plan(new_merged_plan, db_center, other_course)
    # print(tabulate(new_draft_plan, headers="keys", tablefmt="grid"))
    table = create_draft_plan_table(new_draft_plan)
    return Div(
        H2("Plan with 'www.google.org' added for 12 month from current course start"),
        table,
        id="planning-periods"
    )

```

