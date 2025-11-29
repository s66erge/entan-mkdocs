# ~/~ begin <<docs/gong-web-app/center-dashboard.md#libs/cdash.py>>[init]
from fasthtml.common import *

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

    return Main(
        top_menu(session['role']),
        Div(H1("Dashboard"),
            P(f"You are logged in as '{u.email}' with role '{u.role_name}'"),

            P(A("To consult any center gong planning", href="/consult_page")),

            P(A(f"To modify the course planning for one of your centers:  {user_center_list}", href="/planning_page")) if user_centers else None,




            cls="container"
        ),
        cls="container",
    )
# ~/~ end
# ~/~ end
