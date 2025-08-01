# ~/~ begin <<docs/gongprog.md#src\gongUsers.py>>[init]

import secrets
import os
import markdown2
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText

from fasthtml.common import *
# from starlette.testclient import TestClient

css = Style(':root { --pico-font-size: 95% ; --pico-font-family: Pacifico, cursive;}')

# ~/~ begin <<docs/authenticate.md#auth-beforeware>>[init]

login_redir = RedirectResponse('/login', status_code=303)

def before(req, session):
   auth = req.scope['auth'] = session.get('auth', None)
   if not auth: return login_redir

bware = Beforeware(before, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', '/login','/', '/create_magic_link', r'/verify_magic_link/.*'])
# ~/~ end

app, rt = fast_app(live=True, debug=True, before=bware,hdrs=(picolink,css), title="Gong Users", favicon="favicon.ico")

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

SQL_CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY,
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
    user_email TEXT,
    center_name TEXT,
    PRIMARY KEY (user_email, center_name),
    FOREIGN KEY (user_email) REFERENCES users(email),
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
# ~/~ end
# ~/~ begin <<docs/gongprog.md#initialize-database>>[init]

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
    planners.insert(user_email= "spegoff@authentica.eu", center_name= "Mahi")
    planners.insert(user_email= "spegoff@gmail.com", center_name= "Pajjota")
# ~/~ end
# ~/~ begin <<docs/utilities.md#utilities-md>>[init]

# ~/~ begin <<docs/utilities.md#send-email>>[init]

def send_email(subject, body, recipients, password):
    # Create MIMEText email object with the email body
    sender = "spegoff@authentica.eu" 

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    # Connect securely to Gmail SMTP server and login
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
    print("Message sent!")
# ~/~ end
# ~/~ begin <<docs/utilities.md#display-markdown>>[init]

def display_markdown(file_name:str):
    with open(f'md-text/{file_name}.md', "r") as f:
        html_content = markdown2.markdown(f.read())
    return NotStr(html_content)
# ~/~ end
# ~/~ end
# ~/~ begin <<docs/authenticate.md#authenticate-md>>[init]

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
           MyForm("Sign In with Email", "/create_magic_link")
       ), cls="container"
   )
# ~/~ end
# ~/~ begin <<docs/authenticate.md#handling-form>>[init]

@rt('/create_magic_link')
def post(email: str):
    if not email:
       return "Email is required"

# TODO authenticate now the testing email in Railway secrets

    magic_link_token = secrets.token_urlsafe(32)
    magic_link_expiry = datetime.now() + timedelta(minutes=15)
    try:
       user = users[email]
       users.update(email= email, magic_link_token= magic_link_token, magic_link_expiry= magic_link_expiry)
    except NotFoundError:
        return "Email is not registered, try again or send a message to xxx@xxx.xx to get registered"

    print("OS " + os.name)
    if os.name == 'posix':
        base_url = 'https://' + os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    else: # os.name == 'nt'
        base_url = 'http://localhost:5001'

    magic_link = f"{base_url}/verify_magic_link/{magic_link_token}"
    send_magic_link_email(email, magic_link)

    return P("A link to sign in has been sent to your email. Please check your inbox. The link will expire in 15 minutes.", id="success"), HttpHeader('HX-Reswap', 'outerHTML'), Button("Magic link sent", type="submit", id="submit-btn", disabled=True, hx_swap_oob="true")
# ~/~ end
# ~/~ begin <<docs/authenticate.md#send-link>>[init]

def send_magic_link_email(email_address: str, magic_link: str):

   email_subject = "Sign in to The App"
   email_text = f"""
   Hey there,

   Click this link to sign in to The App: {magic_link}

   If you didn't request this, just ignore this email.

   Cheers,
   The App Team
   """
   email_password = os.environ.get('GOOGLE_SMTP_PASS','None')
   if email_password == 'None':
       # Mock email sending by printing to console
       print(f'To: {email_address}\n Subject: {email_subject}\n\n{email_text}')
   else:
       # Send the email using Gmail's SMTP server
       send_email(email_subject, email_text, [email_address], email_password)
# ~/~ end
# ~/~ begin <<docs/authenticate.md#verify-token>>[init]

@rt('/verify_magic_link/{token}')
def get(session, token: str):
   nowstr = f"'{datetime.now()}'"
   try:
       user = users("magic_link_token = ? AND magic_link_expiry > ?", (token, nowstr))[0]
       session['auth'] = user.email
       users.update(email= user.email, magic_link_token= None, magic_link_expiry= None, is_active= True)
       return RedirectResponse('/dashboard')
   except IndexError:
       return "Invalid or expired magic link"
# ~/~ end
# ~/~ begin <<docs/authenticate.md#logout>>[init]
@rt('/logout')
def post(session):
    del session['auth']
    return HttpHeader('HX-Redirect', '/login')
# ~/~ end
# ~/~ end
# ~/~ begin <<docs/gongprog.md#home-page>>[init]
@rt('/')
def home():
    return Main(
        Div(display_markdown("home")),
        A("Login",href="/login", class_="button"),
        cls="container")
# ~/~ end
# ~/~ begin <<docs/dashboard.md#start-admin-md>>[init]

# ~/~ begin <<docs/dashboard.md#dashboard>>[init]

@rt('/dashboard')
def get(session): 
    sessemail = session['auth']
    u = users[sessemail]
    centers = planners("user_email = ?", (u.email,))
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
# ~/~ end
# ~/~ begin <<docs/dashboard.md#admin-page>>[init]

@rt('/admin')
def admin(session):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return Main(
            Nav(Li(A("Dashboard", href="/dashboard"))),
            Div(H1("Access Denied"),
                P("You do not have permission to access this page.")),
            cls="container")
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
                    Tr(Th("Email"), Th("Role"), Th("Action"))
                ),
                Tbody(
                    *[Tr(Td(u.email), Td(u.role_name), Td(A("Delete", href=f"/delete_user/{u.email}"))) for u in users()]
                )
            )
        ),
        Div(
            H2("Centers"),
            Table(
                Thead(
                    Tr(Th("Center Name"), Th("Gong DB Name"), Th("Actions"))
                ),
                Tbody(
                    *[Tr(Td(c.center_name), Td(c.gong_db_name), Td(A("Delete", href=f"/delete_center/{c.center_name}"))) for c in centers()]
                )
            )
        ),
        Div(
            H2("Planners"),
            Table(
                Thead(
                    Tr(Th("User email"), Th("Center Name"), Th("Actions"))
                ),
                Tbody(
                    *[Tr(Td(p.user_email), Td(p.center_name), Td(A("Delete", href=f"/delete_planner/{p.user_email}/{p.center_name}"))) for p in planners()]
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
                Input(type="text", placeholder="User email", id="new_planner_user_email"),
                Input(type="text", placeholder="Center Name", id="new_planner_center_name"),
                Button("Add Planner", hx_post="/add_planner")
            )
        ),

        cls="container",

    )
# ~/~ end
# ~/~ begin <<docs/dashboard.md#delete-routes>>[init]

@rt('/unfinished')
def unfinished():
    return Main(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Div(H1("This feature is not yet implemented.")),
        cls="container"
    )

@rt('/delete_user/{email}')
def delete_user(email:str):
    return unfinished()

@rt('/delete_center/{center_name}')
def delete_center(center_name:str):
    return unfinished()

@rt('/delete_planner/{user_email}/{center_name}')
def delete_planner(user_email:str, center_name:str):
    return unfinished()
# ~/~ end
# ~/~ begin <<docs/dashboard.md#insert-routes>>[init]

@rt('/add_user')
def add_user():
    return HttpHeader('HX-Redirect', '/unfinished')

@rt('/add_center')
def add_center():   
    return HttpHeader('HX-Redirect', '/unfinished')

@rt('/add_planner')
def add_planner():  
    return HttpHeader('HX-Redirect', '/unfinished')          
# ~/~ end
# ~/~ end
# client = TestClient(app)
# print(client.get("/login").text)

serve()
# ~/~ end
