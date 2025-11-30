# ~/~ begin <<docs/gong-web-app/center-consult.md#libs/consul.py>>[init]
from pathlib import Path
from urllib.parse import quote_plus
from fasthtml.common import *
from fasthtml.common import database

from libs.cdash import top_menu

# ~/~ begin <<docs/gong-web-app/center-consult.md#consult-page>>[init]

# @rt('/consult_page')
def consult_page(session, centers):
    # Main consult page: select a center and show its coming_periods.
    Center = centers.dataclass()
    center_names = [c.center_name for c in centers()]
    select = Select(
        Option("Select a center", value="", selected=True, disabled=True),
        *[Option(name, value=name) for name in center_names],
        name="selected_name",
        id="consult-db-select"
    )
    form = Form(
        select,
        Button("Open", type="submit"),
        hx_get="/consult/select_db",
        hx_target="#coming-periods"
    )
    return Main(
        top_menu(session['role']),
        H1("Consult Gong Planning"),
        Div(P("Choose a center:"), form, id="consult-db"),
        H2("Coming periods"),
        Div(id="coming-periods"),            # filled by /consult/select_db
        Div(id="periods-struct"),            # filled by /consult/select_period 
        Div(id="timetables"),                # filled by /consult/select_timetable
        cls="container"
    )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-consult.md#consult-periods>>[init]

# @rt('/consult/select_db')
def consult_select_db(request, centers, db_path):
    # HTMX endpoint: receive form with selected_db in request.form or query_params,
    # return the coming_periods table for that DB. Each row has a Select action that
    # posts period_type (and db) to /consult/select_period.
    params = dict(request.query_params)
    selected_name = params.get("selected_name")
    if not selected_name:
        return Div(P("No center selected."))
    Center = centers.dataclass()
    selected_db = centers[selected_name].gong_db_name

    dbfile_path = Path(db_path) / selected_db
    if not dbfile_path.exists():
        return Div(P(f"Database not found: {selected_db}"))
    db = database(str(dbfile_path))

    # coming_periods table expected fields: start_date, period_type (adjust if field names differ)
    cps = list(db.t.coming_periods())
    pers = list(db.t.periods_struct())

    # Get all period_types from periods_struct and find those not in current rows
    try:
        all_types =  {p.get("period_type") for p in pers}
        seen_types = {p.get("period_type") for p in cps}
        missing_ptypes = sorted(all_types - seen_types)
    except Exception:
        missing_ptypes = []

    # Add also unplanned periods for inspection 
    for mpt in missing_ptypes:
        # Add a row with start_date as 'unplanned' and the missing period_type
        cps.append({"start_date": "unplanned", "period_type": mpt})

    rows = []
    for cp in sorted(cps, key=lambda x: getattr(x, "start_date", "")):
        start = cp.get("start_date")
        ptype = cp.get("period_type")
        # build select link that posts db and period_type to select_period endpoint
        q_db = quote_plus(selected_db)
        q_pt = quote_plus(ptype)
        select_link = A(
            "Select",
            hx_get=f"/consult/select_period?db={q_db}&period_type={q_pt}",
            hx_target="#periods-struct"
        )
        rows.append(Tr(Td(start), Td(ptype), Td(select_link)))

    table = Table(
        Thead(Tr(Th("Start date"), Th("Period type"), Th("Action"))),
        Tbody(*rows)
    )

    return Div(
        Div(table, id="coming-periods-table"),
        Div("", hx_swap_oob="true", id="timetables"),
        Div("", hx_swap_oob="true", id="periods-struct")
    )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-consult.md#consult-structure>>[init]

# @rt('/consult/select_period')
def consult_select_period(request, db_path):
    # HTMX endpoint: show periods_strust rows where period_type matches the selected period_type.
    # Expects query params: db and period_type
    params = dict(request.query_params)
    db_name = params.get("db")
    period_type = params.get("period_type")

    if not db_name or not period_type:
        return Div(P("Missing db or period_type parameter."))

    dbfile_path = Path(db_path) / db_name
    if not dbfile_path.exists():
        return Div(P(f"Database not found: {db_name}"))

    db = database(str(dbfile_path))

    try:
        # periods_struct expected fields: start_date, period_type, other fields...
        rows_src = list(db.t.periods_struct())
    except Exception:
        rows_src = []

    filtered = [r for r in rows_src if (r.get("period_type") or "").strip() == period_type.strip()]

    if not filtered:
        return Div(P(f"No periods found with period_type = {period_type}"))

    tbl_rows = []
    # choose some representative columns (adjust if your schema differs)
    for r in sorted(filtered, key=lambda x: getattr(x, "start_date", "")):
        ptype = r.get("period_type")
        day = str(r.get("day"))
        dtype = r.get("day_type")

        # build select link that posts db, period_type and day_type to select_timetables
        q_db = quote_plus(db_name)
        q_pt = quote_plus(ptype)
        q_dt = quote_plus(dtype)
        select_link = A(
            "Select",
            hx_get=f"/consult/select_timetable?db={q_db}&period_type={q_pt}&day_type={q_dt}",
            hx_target="#timetables"
        )

        tbl_rows.append(Tr(Td(ptype), Td(day), Td(dtype), Td(select_link)))

    table = Table(
        Thead(Tr(Th("Period type"), Th("Day"), Th("Day type"), Th("Action"))),
        Tbody(*tbl_rows)
    )

    return Div(
        Div("", hx_swap_oob="true", id="timetables"),
        H3(f"Structure for period type:'{period_type}', in '{db_name}'"),
        table, id="periods-struct-table"
    )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-consult.md#consult-timetable>>[init]

# @rt('/consult/select_timetables')
def consult_select_timetable(request, db_path):
    # HTMX endpoint: show timetables rows where period_type and day_type match.
    # Expects query params: db, period_type, day_type
    params = dict(request.query_params)
    db_name = params.get("db")
    period_type = params.get("period_type")
    day_type = params.get("day_type")

    if not db_name or not period_type or not day_type:
        return Div(P("Missing db, period_type, or day_type parameter."))

    dbfile_path = Path(db_path) / db_name
    if not dbfile_path.exists():
        return Div(P(f"Database not found: {db_name}"))

    db = database(str(dbfile_path))

    try:
        timetables = list(db.t.timetables())
    except Exception:
        timetables = []

    # Filter where period_type and day_type match
    filtered = [
        t for t in timetables 
        if (t.get("period_type").strip() == period_type.strip() and
            t.get("day_type").strip() == day_type.strip())
    ]

    if not filtered:
        return Div(P(f"No timetables found with period_type = {period_type} and day_type = {day_type}"))

    tbl_rows = []
    for t in filtered:
        # Display all fields from timetables row
        if isinstance(t, dict):
            cells = [Td(str(v)) for v in t.values()]
            headers = list(t.keys())
        else:
            td_dict = getattr(t, "__dict__", {})
            cells = [Td(str(v)) for v in td_dict.values()]
            headers = list(td_dict.keys())

        tbl_rows.append(Tr(*cells))

    # Build headers
    thead = Thead(Tr(*[Th(h) for h in headers]))

    table = Table(thead, Tbody(*tbl_rows))

    return Div(
        H3(f"Timetable for period type: '{period_type}', day type: '{day_type}', in '{db_name}'"),
        table,
        id="timetables-table"
    )
# ~/~ end
# ~/~ end
