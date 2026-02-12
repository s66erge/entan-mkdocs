# ~/~ begin <<docs/gong-web-app/center-dashboard.md#libs/cdash.py>>[init]
from fasthtml.common import *
from libs.utils import display_markdown, Globals

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
def dashboard(session, db): 
    users = db.t.users
    planners = db.t.planners
    Planner = planners.dataclass()
    sessemail = session['auth']
    u = users[sessemail]
    user_planners = planners("user_email = ?", (u.email,))
    user_centers = [(p.center_name) for p in user_planners] 
    user_center_list = ", ".join(user_centers)
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
# ~/~ end
