# Center dashboard page

Will only be reachable for authenticated users.

```{.python file=libs/cdash.py}
from fasthtml.common import *
from libs.feedb import *
from libs.utils import *

<<dashboard>>
```

### Main dashboard

```{.python #dashboard}

# @rt('/dashboard')
def dashboard(session, db): 
    users = db.t.users
    planners = db.t.planners
    sessemail = session['auth']
    u = users[sessemail]
    user_centers = planners("user_email = ?", (u.email,))

    # build center section: single center -> show it, multiple -> ask and show selection menu
    if not user_centers:
        center_section = P("You don't have access to any center.")
    elif len(user_centers) == 1:
        cname = user_centers[0].center_name
        center_section = P(f"You are logged in as '{u.email}' with role '{u.role_name}' and access to gong planning for center: {cname}.")
    else:
        # question + selection menu (HTMX post endpoint /set_current_center can be implemented separately)
        options = [Option(c.center_name, value=c.center_name) for c in user_centers]
        sel = Select(*options, name="selected_center", id="selected-center")
        frm = Form(sel, Button("Work on selected center", hx_post="/set_current_center", hx_target="#dashboard-center"))
        center_section = Div(
            P("Which center do you want to work on?"),
            frm,
            id="dashboard-center"
        )

    return Main(
        Nav(
            Ul(
                Li(A("Admin", href="/admin_page")) if u.role_name == "admin" else None,
                Li(A(href="/unfinished")("Contact")),
                Li(A("About", href="#")),
            ),
            Button("Logout", hx_post="/logout"),
        ),
        Div(H1("Dashboard"), center_section, cls="dashboard-body"),
        cls="container",
    )
```
