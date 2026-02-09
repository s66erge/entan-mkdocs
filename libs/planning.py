# ~/~ begin <<docs/gong-web-app/center-planning.md#libs/planning.py>>[init]
import json
from pathlib import Path
from asyncio import sleep
from urllib.parse import quote_plus
from tabulate import tabulate
from fasthtml.common import *

from libs.utils import display_markdown, isa_dev_computer, Globals
from libs.fetch import fetch_dhamma_courses, check_plan
from libs.dbset import get_central_db


# ~/~ begin <<docs/gong-web-app/center-planning.md#planning-page>>[init]

def abandon_edit(session, db):
    session['shutdown'] = True
    this_center = session["center"]
    session["center"] = ""
    centers = db.t.centers
    Center = centers.dataclass()
    centers.update(center_name=this_center, status="free", current_user="")
    return RedirectResponse('/dashboard')

# Countdown generator for SSE
async def countdown_generator(session, db):
    while session["countdown"] > 0 and not session['shutdown']:
        remaining_seconds = session["countdown"]
        if remaining_seconds > 60:
            messg = f"{int(remaining_seconds // 60)} min."
        else:
            messg = f"{int(remaining_seconds)} sec."
        yield sse_message(messg)
        if remaining_seconds < 2 * session['interval'] and session['interval'] >= 4:
            session['interval'] = session['interval'] // 4
        session["countdown"] = remaining_seconds - session['interval']
        await sleep(session['interval'])

    # When countdown finishes, send final message and call callback only once
    if session["countdown"] <= 0 and not session['shutdown']:
        session['shutdown'] = True
        abandon_edit(session, db)
        yield sse_message("Time is up!")

    # The generator will naturally end here, closing the connection properly
    print("Countdown generator ending.")

def countdown_stream(session, db):
    return EventStream(countdown_generator(session, db))

# @rt('/planning_page')
def planning_page(session, request, db):
    params = dict(request.query_params)
    selected_name = params.get("selected_name")
    session["center"] = selected_name
    centers = db.t.centers
    Center = centers.dataclass()
    q_center = quote_plus(selected_name)
    this_user= session['auth']
    # FIXME use SQL db commit for the following 5 lines 
    status_bef = centers[selected_name].status
    if status_bef == "free":
        centers.update(center_name=selected_name, status="edit", current_user=this_user)
    busy_user = centers[selected_name].current_user
    timezone = centers[selected_name].timezone
    if status_bef != "free" or busy_user != this_user:
        return Div(
            P(f"Anoher user has initiated a session to modify this center gong planning. To bring new changes, you must wait until the modified planning has been installed into the local center computer. This will happen at 3am, local time of the center: {timezone}"),
            P("If you want to consult any center in the mean time, go to the dashboard. Otherwise please logout."),
            Span(
                A("dashboard", href="/dashboard"),
                Span(style="display: inline-block; width: 20px;"),
                Button("Logout", hx_post="/logout"),
                Span(style="display: inline-block; width: 20px;"),
                A("set FREE",href="/planning/abandon_edit") if isa_dev_computer() else None,        
            )
        )

    session['shutdown'] = False
    if session["countdown"] == 0:
        session["countdown"] = Globals.INITIAL_COUNTDOWN
        session['interval'] = Globals.INITIAL_INTERVAL
    print("at plan menu")
    print(session)
    return Main(
        Div(display_markdown("planning-t")),
        Span(
            Button(f"Modify {selected_name} planning",
                hx_get=f"/planning/load_dhamma_db?selected_name={selected_name}",
                hx_target="#planning-periods"),
            Span(style="display: inline-block; width: 20px;"),
            Button(f"Modify {selected_name} course types / timetables",
                hx_get="/unfinished?goto_dash=NO",
                hx_target="#planning-periods"),
            Span(style="display: inline-block; width: 20px;"),
            A("return NO CHANGES",href=f"/planning/abandon_edit",),
            Span(style="display: inline-block; width: 20px;"),
            Span("Remainning time: "),
            Span(id="timer", 
                hx_ext="sse",
                sse_connect=f"/countdown",
                sse_swap="message",
                cls="timer-display"
                ),
            Script("""
            function checkTimerAndRedirect() {
                const timerDiv = document.getElementById('timer');
                if (!timerDiv) return;            
                const text = timerDiv.textContent || timerDiv.innerText;          
                if (text === "Time is up!") {
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 1000); // Redirect after 1 second
                }
            }
            // Start polling - STORE the interval ID
            setInterval(checkTimerAndRedirect, 1000);

            """)
        ),

        P(""),       
        Div(id="planning-periods"),          # filled by /planning/load_dhamma_db
        cls="container"
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
def load_dhamma_db(session, request, db):
    #centers = db.t.centers
    #params = dict(request.query_params)
    #selected_name = params.get("selected_name")
    #if not selected_name:
    #    return Div(P("No center selected."))
    #Center = centers.dataclass()
    # this_center = centers[selected_name].center_name
    this_center = session["center"]
    q_center = quote_plus(this_center)
    """
    this_user= session['auth']
    # FIXME use SQL db commit for the following 5 lines 
    status_bef = centers[this_center].status
    if status_bef == "free":
        centers.update(center_name=this_center, status="edit", current_user=this_user)
    busy_user = centers[this_center].current_user
    timezone = centers[this_center].timezone
    if status_bef != "free" or busy_user != this_user:
        return Div(
            P(f"Anoher user has initiated a session to modify this center gong planning. To bring new changes, you must wait until the modified planning has been installed into the local center computer. This will happen between 1am and 3am, local time of the center: {timezone}"),            
            )
    """
    return Div(
        P(" Loading from dhamma.org ..."),
        Div(hx_get=f"/planning/show_dhamma?selected_name={q_center}", 
            hx_target="#planning-periods",
            hx_trigger="load",  # Triggers when this div loads
            style="display: none;"),
        id="planning-periods"
    )

# @rt('/planning/show_dhamma')
def show_dhamma(session, request, db, db_path):
    centers = db.t.centers
    #params = dict(request.query_params)
    #selected_name = params.get("selected_name")
    #if not selected_name:
    #    return Div(P("No center selected."))
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

# ~/~ end
# ~/~ end
