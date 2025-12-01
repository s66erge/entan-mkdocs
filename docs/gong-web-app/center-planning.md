# Center consult page

Will only be reachable for authenticated users.

```{.python file=libs/planning.py}
from pathlib import Path
from urllib.parse import quote_plus
from tabulate import tabulate
from fasthtml.common import *
from fasthtml.common import database

from libs.cdash import top_menu
from libs.fetch import fetch_dhamma_courses, check_plan

<<planning-page>>
```


### Planning page

```{.python #planning-page}

# @rt('/planning_page')
def planning_page(session, db_central):
    # Main consult page: select a center and show its coming_periods.
    planners = db_central.t.planners
    sessemail = session['auth']
    user_planners = planners("user_email = ?", (sessemail,))
    center_names = [(p.center_name) for p in user_planners] 

    select = Select(
        Option("Select a center", value="", selected=True, disabled=True),
        *[Option(name, value=name) for name in center_names],
        name="selected_name",
        id="planning-db-select"
    )
    form = Form(
        select,
        Button("Open", type="submit"),
        hx_get="/planning/get_dhamma_db",
        hx_target="#planning-periods"
    )
    return Main(
        top_menu(session['role']),
        H1("Change Gong Planning"),
        Div(
            P("Choose a center:"),
            form,
            id="consult-db"
        ) if len(center_names) > 1 else None,
        Button(
            f"{str(center_names[0])}", 
            hx_get=f"/planning/get_dhamma_db?selected_name={str(center_names[0])}",
            hx_target="#planning-periods",
            hx_trigger="load"
        ) if len(center_names) == 1 else None,
        H2("Plan with 'www.google.org' added for 12 month from current course start"),
        Div(id="planning-periods"),          # filled by /planning/get_dhamma_db
        cls="container"
    )

# @rt('/planning/get_dhamma_db')
def get_dhamma_db(request, centers, db_path):
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

    new_merged_plan = fetch_dhamma_courses(selected_name, 12, 0)

    new_draft_plan = check_plan(new_merged_plan, db_center)

    print(tabulate(new_draft_plan, headers="keys", tablefmt="grid"))

    rows = []
    # Color ptype in red if equal to UNKNOWN
    for plan_line in sorted(new_draft_plan, key=lambda x: getattr(x, "start_date", "")):
        start = plan_line.get("start_date")
        ptype = plan_line.get("period_type")
        source = plan_line.get("source")
        check = plan_line.get("check")
        course = plan_line.get("course_type")
        # Color period_type red if it's UNKNOWN
        if ptype == "UNKNOWN":
            ptype_cell = Td(ptype, style="background: red")
        else:
            ptype_cell = Td(ptype)
        if not check.startswith("OK"):
            check_cell = Td(check, style="background: red")
        else:
            check_cell = Td(check)
        # CONTINOW build amnd show 
        rows.append(Tr(Td(start), ptype_cell, Td(source), check_cell, Td(course)))

    table = Table(
        Thead(Tr(Th("Start date"), Th("Period type"), Th("source"), Th("check"),
        Th("Dhamma.org center course"))),
        Tbody(*rows)
    )

    return Div(
        Div(table, id="coming-periods-table"),
        # Div("", hx_swap_oob="true", id="timetables"),
        # Div("", hx_swap_oob="true", id="periods-struct")
    )
```

