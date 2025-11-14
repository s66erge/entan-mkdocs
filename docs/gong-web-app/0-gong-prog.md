# Gong main program 

### Program start


```{.python file=main.py}

import os
import shutil
from functools import wraps
from fasthtml.common import *
# from starlette.testclient import TestClient

from libs import *

css = Style(':root {--pico-font-size: 95% ; --pico-font-family: Pacifico, cursive;}')

def before(req, session):
   auth = req.scope['auth'] = session.get('auth', None)
   if not auth: return RedirectResponse('/login', status_code=303)

bware = Beforeware(before, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', '/login','/', '/create_magic_link', r'/verify_magic_link/.*'])

app, rt = fast_app(live=True, debug=True, title="Gong Users", favicon="favicon.ico",
                   before=bware, hdrs=(picolink,css),)

db = dbset.get_database()
dbset.create_tables(db)

users = db.t.users
roles = db.t.roles
centers = db.t.centers
planners = db.t.planners

Role = roles.dataclass()
Center = centers.dataclass()
Planner = planners.dataclass()
User = users.dataclass()

dbset.init_data(roles, centers, users, planners)

def admin_required(handler):
    @wraps(handler)
    def wrapper(session, *args, **kwargs):
        # Assuming user info is in session
        sessemail = session['auth']
        u = users[sessemail]
        if not u or not u.role_name == "admin":
            # Redirect to login or unauthorized page if not admin
            return Main(
                Nav(Li(A("Dashboard", href="/dashboard"))),
                Div(H1("Access Denied"),
                    P("You do not have permission to access this page.")),
                cls="container")
        # Proceed if user is admin
        return handler(session, *args, **kwargs)
    return wrapper

@rt('/login')
def get():
    return auth.login()

@rt('/create_magic_link')
def post(email: str):
    return auth.create_link(email, users)

@rt('/verify_magic_link/{token}')
def get(session, token: str):
    return auth.verify_link(session, token, users) 

<<admin-show-md>>
<<admin-change-md>>

# client = TestClient(app)
# print(client.get("/login").text)

@rt('/')
def home():
    return Main(
        Div(utils.display_markdown("home")),
        A("Login",href="/login", class_="button"),
        cls="container"
    )

@rt('/dashboard')
def get(session): 
    sessemail = session['auth']
    u = users[sessemail]
    centers = planners("user_email = ?", (u.email,))
    center_names = ", ".join(c.center_name for c in centers)
    return Main(
        Nav(
            Ul(
                Li(A("Admin", href="/admin_page")) if u.role_name == "admin" else None ,
                Li(A(href="/unfinished")("Contact")),
                Li(A("About", href="#")),
            ), 
            Button("Logout", hx_post="/logout"),
        ),
        Div(H1("Dashboard"), P(f"You are logged in as '{u.email}' with role '{u.role_name}' and access to gong planning for center(s) : {center_names}.")),
        cls="container",
    )

@rt('/logout')
def post(session):
    del session['auth']
    return HttpHeader('HX-Redirect', '/login')

@rt('/unfinished')
def unfinished():
    return Main(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Div(H1("This feature is not yet implemented.")),
        cls="container"
    )

@rt('/db_error')
def db_error(session, etext: str):
    return Html(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Head(Title("Database error")),
        Body(Div(feedb.feedback_to_user({'error': 'db_error', 'etext': f'{etext}'}))),
        (A("Dashboard", href="/dashboard")),
        cls="container"
    )

serve()
```
