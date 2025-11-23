# Center dashboard page

Will only be reachable for authenticated users.

```{.python file=libs/cdash.py}
from fasthtml.common import *

DATA_FOLDER = Path("data")  # adjust if your gong DBs are elsewhere

<<dashboard>>
```

### Main dashboard

```{.python #dashboard}

def top_menu(role):
    return Nav(
            Ul(
                Li(A("Admin", href="/admin_page")) if role == "admin" else None,
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
            P(f"You can modify the gong planning for: {user_center_list}") if user_centers else None,
            H3(A("To consult a specific center gong planning", href="/consult_page")),




            cls="container"
        ),
        cls="container",
    )
```
