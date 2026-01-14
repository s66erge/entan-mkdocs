# Center consult page

Will only be reachable for authenticated users.

```{.python file=libs/planning.py}
import json
from pathlib import Path
from urllib.parse import quote_plus
from tabulate import tabulate
from fasthtml.common import *

from libs.cdash import top_menu
from libs.fetch import fetch_dhamma_courses, check_plan

<<planning-page>>
```


### Planning page

```{.python #planning-page}
# @rt('/planning_page')
def planning_page(session, request, db_central):

    params = dict(request.query_params)
    selected_name = params.get("selected_name")

    return Main(
        top_menu(session['role']),
        H1(f"Change Gong Planning - {selected_name}"),

        Div(hx_get=f"/planning/load_dhamma_db?selected_name={selected_name}",
            hx_target="#planning-periods",
            hx_trigger="load",
            style="display: none;"),

        H2("Plan with 'www.google.org' added for 12 month from current course start"),
        Div(id="planning-periods"),          # filled by /planning/load_dhamma_db
        cls="container"
    )

def create_draft_plan_table(draft_plan):
    # Create an HTML table from a draft plan list of dictionaries.
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
    centers = db.t.centers
    params = dict(request.query_params)
    selected_name = params.get("selected_name")
    if not selected_name:
        return Div(P("No center selected."))
    Center = centers.dataclass()

    this_center = centers[selected_name].center_name
    q_center = quote_plus(this_center)
    this_user= session['auth']
    # CONTINOW START TIMER + use SQL db commit for the following 5 lines 
    status_bef = centers[selected_name].status
    if status_bef == "free":
        centers.update(center_name=this_center, status="edit", current_user=this_user)
    busy_user = centers[selected_name].current_user
    timezone = centers[selected_name].timezone
    if status_bef != "free" or busy_user != this_user:
        return Div(
            P(f"Anoher user has initiated a session to modify this center gong planning. To bring new changes, you must wait until the modified planning has been installed into the local center computer. This will happen between 1am and 3am, local time of the center: {timezone}"),
            A("Force status to 'free' - ONLY FOR DEV !",
                hx_get=f"/planning/set_free?center_name={q_center}",
                hx_target="#planning-periods"
            ) 
            )

    return Div(
        P(" Loading from dhamma.org ..."),
        Div(hx_get=f"/planning/show_dhamma?selected_name={q_center}", 
            hx_target="#planning-periods",
            hx_trigger="load",  # Triggers when this div loads
            style="display: none;"),
        id="planning-periods"
    )

# @rt('/planning/show_dhamma')
def show_dhamma(request, db, db_path):
    centers = db.t.centers
    params = dict(request.query_params)
    selected_name = params.get("selected_name")
    if not selected_name:
        return Div(P("No center selected."))
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

    # CONTINOW TEMPORARY free access to center planning
    centers.update(center_name=selected_name, status="free", current_user="")

    return Div(
        table,
        id="planning-periods"
    )

#@rt('/planning/set_free')
def set_free(request, db):
    centers = db.t.centers
    params = dict(request.query_params)
    this_center = params.get("center_name")
    if not this_center:
        return Div(P("No center selected."))
    Center = centers.dataclass()
    centers.update(center_name=this_center, status="free", current_user="")
    return Div("Status set to 'free'")
```

