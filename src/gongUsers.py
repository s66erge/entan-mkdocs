# ~/~ begin <<docs/gongprog.md#src\gongUsers.py>>[init]

from fasthtml.common import *
# from starlette.testclient import TestClient
import secrets
from datetime import datetime, timedelta

css = Style(':root { --pico-font-size: 90% ; --pico-font-family: Pacifico, cursive;}')

# ~/~ begin <<docs/authenticate.md#auth-beforeware>>[init]

login_redir = RedirectResponse('/login', status_code=303)

def before(req, session):
   auth = req.scope['auth'] = session.get('auth', None)
   if not auth: return login_redir

bware = Beforeware(before, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', '/login', '/send_magic_link', r'/verify_magic_link/.*'])
# ~/~ end

#app, rt = fast_app(live=True, debug=True, before=bware,hdrs=(picolink, css))
app, rt = fast_app(live=True, debug=True, before=bware,hdrs=(picolink,css))

# ~/~ begin <<docs/gongprog.md#setup-database>>[init]

db = database('data/gongUsers.db')

SQL_CREATE_ROLES = """
CREATE TABLE IF NOT EXISTS roles (
    role_name TEXT PRIMARY KEY,
    description TEXT
);
"""

SQL_CREATE_CENTERS = """
CREATE TABLE IF NOT EXISTS centers (
    center_name TEXT PRIMARY KEY,
    gong_db_name TEXT
);
"""
# TODO suppress user id and use email instead EVERYWHERE !!!
SQL_CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    name TEXT,
    role_name TEXT,
    magic_link_token TEXT,
    magic_link_expiry TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (role_name) REFERENCES roles(role_name)
);

"""

SQL_CREATE_PLANNERS = """
CREATE TABLE IF NOT EXISTS planners (
    userid INTEGER,
    center_name TEXT,
    PRIMARY KEY (userid, center_name),
    FOREIGN KEY (userid) REFERENCES users(id),
    FOREIGN KEY (center_name) REFERENCES centers(center_name)
);
"""

db.execute(SQL_CREATE_ROLES)
db.execute(SQL_CREATE_CENTERS)
db.execute(SQL_CREATE_USERS)
db.execute(SQL_CREATE_PLANNERS)

users = db.t.users
roles = db.t.roles
centers = db.t.centers
planners = db.t.planners

Role = roles.dataclass()
Center = centers.dataclass()
Planner = planners.dataclass()
User = users.dataclass()

# Check if any table(s) is(are) empty and insert default values if needed
if not roles():
    roles.insert(role_name="admin", description="administrator")
    roles.insert(role_name="user", description="regular user")

if not centers():
    centers.insert(center_name="Mahi", gong_db_name="mahi.db")
    centers.insert(center_name="Pajjota", gong_db_name="pajjota.db")

if not users():
    users.insert(email="spegoff@authentica.eu", name="sp1", role_name="admin", is_active=True, magic_link_token=None, magic_link_expiry=None)
    users.insert(email="spegoff@gmail.com", name="sp2", role_name="user", is_active=True)

if not planners():
    sp1id = users("name='sp1'")[0].id
    sp2id = users("name='sp2'")[0].id
    print(sp1id, " ", sp2id)
    planners.insert(userid= sp1id, center_name="Mahi")
    planners.insert(userid= sp2id, center_name="Pajjota")
# ~/~ end
# ~/~ begin <<docs/authenticate.md#authenticate>>[init]

# ~/~ begin <<docs/authenticate.md#build-serve-login-form>>[init]
def MyForm(btn_text: str, target: str):
   return Form(
       Div(
           Div(
               Input(id='email', type='email', placeholder='foo@bar.com'),
           ),
       ),
       Button(btn_text, type="submit", id="submit-btn"),
       P(id="error"),
       hx_post=target,
       hx_target="#error",
       hx_disabled_elt="#submit-btn"
   )

@rt('/login')
def get():   
   return Main(
       Div(
           H1("Sign In"),
           P("Enter your email to sign in to The App."),
           MyForm("Sign In with Email", "/send_magic_link")
       ), cls="container"
   )
# ~/~ end
# ~/~ begin <<docs/authenticate.md#handling-form>>[init]
@rt('/send_magic_link')
def post(email: str):
   if not email:
       return "Email is required"

   magic_link_token = secrets.token_urlsafe(32)
   magic_link_expiry = datetime.now() + timedelta(minutes=15)
   try:
       user = users("email = ?",(email,))[0]
       users.update(id= user.id, magic_link_token= magic_link_token, magic_link_expiry= magic_link_expiry)
   except IndexError:
        return "Email is not registered, try again or send a message to xxx@xxx.xx to get registered"

   magic_link = f"http://localhost:5001/verify_magic_link/{magic_link_token}"
   send_magic_link_email(email, magic_link)

   return P("A link to sign in has been sent to your email. Please check your inbox. The link will expire in 15 minutes.", id="success"), HttpHeader('HX-Reswap', 'outerHTML'), Button("Magic link sent", type="submit", id="submit-btn", disabled=True, hx_swap_oob="true")
# ~/~ end
# ~/~ begin <<docs/authenticate.md#send-link>>[init]
def send_magic_link_email(email: str, magic_link: str):

   email_content = f"""
   To: {email}
   Subject: Sign in to The App
   ============================

   Hey there,

   Click this link to sign in to The App: {magic_link}

   If you didn't request this, just ignore this email.

   Cheers,
   The App Team
   """
   # Mock email sending by printing to console
   print(email_content)
# ~/~ end
# ~/~ begin <<docs/authenticate.md#verify-token>>[init]
@rt('/verify_magic_link/{token}')
def get(session, token: str):
   nowstr = f"'{datetime.now()}'"
   try:
       user = users("magic_link_token = ? AND magic_link_expiry > ?", (token, nowstr))[0]
       session['auth'] = user.email
       users.update(id= user.id, magic_link_token= None, magic_link_expiry= None, is_active= True)
       return RedirectResponse('/dashboard')
   except IndexError:
       return "Invalid or expired magic link"
# ~/~ end
# ~/~ end
# ~/~ begin <<docs/dashboard.md#starting-page>>[init]

@rt('/dashboard')
def get(session): 
    sessemail = session['auth']
    u = users("email = ?", (sessemail,))[0]
    centers = planners("userid = ?", (u.id,))
    center_names = ", ".join(c.center_name for c in centers)
    return Main(
        Nav(
            Ul(
                Li(A("Admin", href="/admin")) if u.role_name == "admin" else None ,
                Li(A("Contact", href="#")),
                Li(A("About", href="#")),
            ), 
            Button("Logout", hx_post="/logout"),
        ),
        Div(H1("Dashboard"), P(f"You are logged in as '{u.email}' with role '{u.role_name}' and access to gong planning for center(s) : {center_names}.")),
        cls="container",
    )

@rt('/admin')
def admin(session):
    sessemail = session['auth']
    u = users("email = ?", (sessemail,))[0]
    if u.role_name != "admin":
        return Main(Div(H1("Access Denied"), P("You do not have permission to access this page.")), cls="container")
    
    return Main(
        Nav(
            Ul(
                Li(A("Dashboard", href="/dashboard")),
                Li(A("Contact", href="#")),
                Li(A("About", href="#")),
            ), 
            Button("Logout", hx_post="/logout"),
        ),
        Div(H1("Admin Dashboard"), P("Here you can manage users, centers, and planners.")),
        Div(
            H2("Users"),
            Table(
                Thead(
                    Tr(
                        Th("User ID"), 
                        Th("Email"), 
                        Th("Role"), 
                        Th("Actions")
                    )
                ),
                Tbody(
                    *[Tr(Td(u.id), Td(u.email), Td(u.role_name), Td(A("Edit", href=f"/edit_user/{u.id}"))) for u in users()]
                )
            )
        ),
        Div(
            H2("Centers"),
            Table(
                Thead(
                    Tr(
                        Th("Center Name"), 
                        Th("Gong DB Name"), 
                        Th("Actions")
                    )
                ),
                Tbody(
                    *[Tr(Td(c.center_name), Td(c.gong_db_name), Td(A("Edit", href=f"/edit_center/{c.center_name}"))) for c in centers()]
                )
            )
        ),
        Div(
            H2("Planners"),
            Table(
                Thead(
                    Tr(
                        Th("User ID"), 
                        Th("Center Name"), 
                        Th("Actions")
                    )
                ),
                Tbody(
                    *[Tr(Td(p.userid), Td(p.center_name), Td(A("Edit", href=f"/edit_planner/{p.userid}/{p.center_name}"))) for p in planners()]
                )
            )
        ),
        Div(
            H2("Add New User"),
            Form(
                Input(type="email", placeholder="User Email", id="new_user_email"),
                Select( 
                    Option("Admin", value="admin"),
                    Option("User", value="user"),
                    id="new_user_role", name="role_name"),
                Button("Add User", hx_post="/add_user")
            )
        ),
        Div(
            H2("Add New Center"),
            Form(
                Input(type="text", placeholder="Center Name", id="new_center_name"),
                Input(type="text", placeholder="Gong DB Name", id="new_gong_db_name"),
                Button("Add Center", hx_post="/add_center")
            )
        ),
        Div(
            H2("Add New Planner"),
            Form(
                Input(type="number", placeholder="User ID", id="new_planner_userid"),
                Input(type="text", placeholder="Center Name", id="new_planner_center_name"),
                Button("Add Planner", hx_post="/add_planner")
            )
        ),

        cls="container",
        
    )
# ~/~ end

# ~/~ begin <<docs/authenticate.md#logout>>[init]
@rt('/logout')
def post(session):
    del session['auth']
    return HttpHeader('HX-Redirect', '/login')
# ~/~ end
# client = TestClient(app)
# print(client.get("/login").text)

serve()
# ~/~ end
