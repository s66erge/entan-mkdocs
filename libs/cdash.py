# ~/~ begin <<docs/gong-web-app/center-dashboard.md#libs/cdash.py>>[init]
from myFasthtml import *
from pathlib import Path
import shutil
from libs.utils import display_markdown, Globals
from libs.dbset import get_db_path

# ~/~ begin <<docs/gong-web-app/center-dashboard.md#dashboard>>[init]

def top_menu(role):
    return Nav(
            Ul(
                Li(A("Admin", href="/admin_page")) if role == "admin" else None,
                Li(A("Dashboard", href="/dashboard")),
                Li(A("Contact", href="/unfinished")),
                Li(A("About", href="/unfinished")),
            ),
            Button("Logout", hx_post="/logout"),
    )

# @rt('/dashboard')
def dashboard(session, users, planners):
    sessemail = session['auth']
    u = users[sessemail]
    user_planners = planners("user_email = ?", (u.email,))
    user_centers = [(p.center_name) for p in user_planners] 
    select = Select(
        Option("Select a center", value="", selected=True),
        *[Option(name, value=name) for name in user_centers],
        name="selected_name",
        id="planning-db-select",
        required=True
    )
    form = Form(
        select,
        Button("MODIFY", type="submit"),
        action="/planning_page",
        method ="get",
    )
    return Main(
        top_menu(session['role']),
        Div(Div(display_markdown("dashboard-t")),
            P(f"You are logged in as '{u.email}' with role '{u.role_name}'"),
            P(""),
            P(A("CONSULT", href="/consult_page")),
            Div(
                P("Choose one of the centers you can modify:"),
                form
            ) if len(user_centers) >= 1 else None,
            cls="container"
        ),
        cls="container",
    )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-dashboard.md#save-center-db>>[init]

def save_center_db(session, centers, csms):
    center_name = session['center']
    state_mach = csms[center_name]
    state_mach.saving_changes()

    source_db_file = Path(get_db_path() + "/" + center_name.lower() + ".ok.db")
    dest_db_file = Path(get_db_path() + "/" + center_name.lower() + ".sending.db")
    shutil.copy2(source_db_file, dest_db_file)
    dest_db = database(dest_db_file)
    dest_db.execute("DELETE FROM coming_periods")

    print(f"state: {state_mach.current_state.id}")
    state_mach.file_trans_done()
    state_mach.db_prod_done()
    print(f"state: {state_mach.current_state.id}")
    return  Redirect('/dashboard')

# ~/~ end
# ~/~ end
