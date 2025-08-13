# ~/~ begin <<docs/gong-program/agongprog.md#main.py>>[init]

import secrets
import os
import socket
import markdown2
import smtplib
import shutil
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from fasthtml.common import *
# from starlette.testclient import TestClient

css = Style(':root {--pico-font-size: 95% ; --pico-font-family: Pacifico, cursive;}')

# ~/~ begin <<docs/gong-program/authenticate.md#auth-beforeware>>[init]

login_redir = RedirectResponse('/login', status_code=303)

def before(req, session):
   auth = req.scope['auth'] = session.get('auth', None)
   if not auth: return login_redir

bware = Beforeware(before, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', '/login','/', '/create_magic_link', r'/verify_magic_link/.*'])
# ~/~ end

app, rt = fast_app(live=True, debug=True, before=bware,hdrs=(picolink,css), title="Gong Users", favicon="favicon.ico")

# ~/~ begin <<docs/gong-program/agongprog.md#setup-database>>[init]

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
# ~/~ begin <<docs/gong-program/agongprog.md#initialize-database>>[init]

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
# ~/~ begin <<docs/gong-program/utilities.md#utilities-md>>[init]

# ~/~ begin <<docs/gong-program/utilities.md#isa-dev-computer>>[init]

DEV_COMPUTERS = ["ASROCK-MY-OFFICE","DESKTOP-UIPS8J2","serge-virtual-linuxmint"]
def isa_dev_computer():
    hostname = socket.gethostname()
    return hostname in DEV_COMPUTERS
# ~/~ end
# ~/~ begin <<docs/gong-program/utilities.md#send-email>>[init]

def send_email(subject, body, recipients):
    sender = os.environ.get('GOOGLE_SMTP_USER') 
    password = os.environ.get('GOOGLE_SMTP_PASS')
    # Create MIMEText email object with the email body
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
# ~/~ begin <<docs/gong-program/utilities.md#display-markdown>>[init]

def display_markdown(file_name:str):
    with open(f'md-text/{file_name}.md', "r") as f:
        html_content = markdown2.markdown(f.read())
    return NotStr(html_content)
# ~/~ end
# ~/~ end
# ~/~ begin <<docs/gong-program/authenticate.md#authenticate-md>>[init]

# ~/~ begin <<docs/gong-program/authenticate.md#build-serve-login-form>>[init]
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
# ~/~ begin <<docs/gong-program/authenticate.md#handling-form>>[init]

@rt('/create_magic_link')
def post(email: str):
    if not email:
       return "Email is required"

    magic_link_token = secrets.token_urlsafe(32)
    magic_link_expiry = datetime.now() + timedelta(minutes=15)
    try:
       user = users[email]
       users.update(email= email, magic_link_token= magic_link_token, magic_link_expiry= magic_link_expiry)
    except NotFoundError:
        return "Email is not registered, try again or send a message to xxx@xxx.xx to get registered"

    print("name " + socket.gethostname())
    if not isa_dev_computer():
        base_url = 'https://' + os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    else: 
        base_url = 'http://localhost:5001'

    magic_link = f"{base_url}/verify_magic_link/{magic_link_token}"
    send_magic_link_email(email, magic_link)

    return P("A link to sign in has been sent to your email. Please check your inbox. The link will expire in 15 minutes.", id="success"), HttpHeader('HX-Reswap', 'outerHTML'), Button("Magic link sent", type="submit", id="submit-btn", disabled=True, hx_swap_oob="true")
# ~/~ end
# ~/~ begin <<docs/gong-program/authenticate.md#send-link>>[init]

def send_magic_link_email(email_address: str, magic_link: str):

   email_subject = "Sign in to The App"
   email_text = f"""
   Hey there,

   Click this link to sign in to The App: {magic_link}

   If you didn't request this, just ignore this email.

   Cheers,
   The App Team
   """
   email_sender = os.environ.get('GOOGLE_SMTP_USER','None')
   if email_sender == 'None':
       print(f'To: {email_address}\n Subject: {email_subject}\n\n{email_text}')
   else:
       send_email(email_subject, email_text, [email_address])
# ~/~ end
# ~/~ begin <<docs/gong-program/authenticate.md#verify-token>>[init]

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
# ~/~ begin <<docs/gong-program/authenticate.md#logout>>[init]
@rt('/logout')
def post(session):
    del session['auth']
    return HttpHeader('HX-Redirect', '/login')
# ~/~ end
# ~/~ end
# ~/~ begin <<docs/gong-program/agongprog.md#home-page>>[init]
@rt('/')
def home():
    return Main(
        Div(display_markdown("home")),
        A("Login",href="/login", class_="button"),
        cls="container")
# ~/~ end
# ~/~ begin <<docs/gong-program/dashboard.md#start-dash-md>>[init]

# ~/~ begin <<docs/gong-program/dashboard.md#dashboard>>[init]

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
                Li(A("Contact", href="#")),
                Li(A("About", href="#")),
            ), 
            Button("Logout", hx_post="/logout"),
        ),
        Div(H1("Dashboard"), P(f"You are logged in as '{u.email}' with role '{u.role_name}' and access to gong planning for center(s) : {center_names}.")),
        cls="container",
    )

@rt('/unfinished')
def unfinished():
    return Main(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Div(H1("This feature is not yet implemented.")),
        cls="container"
    )
# ~/~ end
# ~/~ end
# ~/~ begin <<docs/gong-program/admin-show.md#admin-show-md>>[init]

# ~/~ begin <<docs/gong-program/admin-show.md#show-users>>[init]
def show_users():
    return Main( 
        Div(
        Table(
        H2("Users"),
            Thead(
                Tr(Th("Email"), Th("Name"), Th("Role"), Th("Active"), Th("Action"))
            ),
            Tbody(
                *[Tr(
                    Td(u.email), 
                    Td(u.name or ""), 
                    Td(u.role_name), 
                    Td("Yes" if u.is_active else "No"),
                    Td(A("Delete", href=f"/delete_user/{u.email}", 
                        onclick="return confirm('Are you sure you want to delete this user?')"))
                ) for u in users()]
            )
        )
    ),
    Div(
        H4("Add New User"),
        Form(
            Input(type="email", placeholder="User Email", name="new_user_email", required=True),
            Select( 
                Option("Select Role", value="", selected=True, disabled=True),
                Option("Admin", value="admin"),
                Option("User", value="user"),
                    name="role_name", required=True),
            Button("Add User", type="submit"),
            method="post",
            action="/add_user"
            )
        )    
    )
# ~/~ end
# ~/~ begin <<docs/gong-program/admin-show.md#show-centers>>[init]
def show_centers():
    return Main(
        Div(
        H2("Centers"),
        Table(
            Thead(
                Tr(Th("Center Name"), Th("Gong DB Name"), Th("Actions"))
            ),
            Tbody(
                *[Tr(
                    Td(c.center_name), 
                    Td(c.gong_db_name), 
                    Td(A("Delete", href=f"/delete_center/{c.center_name}",
                        onclick="return confirm('Are you sure you want to delete this center?')"))
                    ) for c in centers()]
                )
            )
        ),
        Div(
            H4("Add New Center"),
            Form(
                Input(type="text", placeholder="Center Name", name="new_center_name", required=True),
                Input(type="text", placeholder="Gong DB Name (without .db)", name="new_gong_db_name", required=True),
                Small("The database file will be created as a copy of mahi.db"),
                Button("Add Center", type="submit"),
                method="post",
                action="/add_center"
            )
        )
    )
# ~/~ end
# ~/~ begin <<docs/gong-program/admin-show.md#show-planners>>[init]
def show_planners():
    return Main(
        Div(
            H2("Planners"),
            Table(
                Thead(
                    Tr(Th("User Email"), Th("Center Name"), Th("Actions"))
                ),
                Tbody(
                    *[Tr(
                        Td(p.user_email), 
                        Td(p.center_name), 
                        Td(A("Delete", href=f"/delete_planner/{p.user_email}/{p.center_name}",
                             onclick="return confirm('Are you sure you want to delete this planner association?')"))
                    ) for p in planners()]
                )
            )
        ),
        Div(
            H4("Add New Planner"),
            Form(
                Select(
                    Option("Select User", value="", selected=True, disabled=True),
                    *[Option(u.email, value=u.email) for u in users()],
                    name="new_planner_user_email", required=True
                ),
                Select(
                    Option("Select Center", value="", selected=True, disabled=True),
                    *[Option(c.center_name, value=c.center_name) for c in centers()],
                    name="new_planner_center_name", required=True
                ),
                Button("Add Planner", type="submit"),
                method="post",
                action="/add_planner"
            )
        )
    )
# ~/~ end
# ~/~ begin <<docs/gong-program/admin-show.md#admin-page>>[init]

@rt('/admin_page')
def admin(session, request):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return Main(
            Nav(Li(A("Dashboard", href="/dashboard"))),
            Div(H1("Access Denied"),
                P("You do not have permission to access this page.")),
            cls="container")

    # Handle success and error messages
    query_params = dict(request.query_params)
    message_div = None

    if 'success' in query_params:
        success_messages = {
            'user_added': 'User added successfully!',
            'center_added': 'Center added successfully!',
            'planner_added': 'Planner association added successfully!',
            'user_deleted': 'User deleted successfully!',
            'center_deleted': 'Center and associated database deleted successfully!',
            'planner_deleted': 'Planner association deleted successfully!'
        }
        message = success_messages.get(query_params['success'], 'Operation completed successfully!')
        message_div = Div(P(message), style="color: #d1f2d1; background: #0f5132; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #198754; font-weight: 500;")

    elif 'error' in query_params:
        error_messages = {
            'missing_fields': 'Please fill in all required fields.',
            'user_exists': 'User with this email already exists.',
            'center_exists': 'Center with this name already exists.',
            'planner_exists': 'This planner association already exists.',
            'user_not_found': 'User not found.',
            'center_not_found': 'Center not found.',
            'invalid_role': 'Invalid role selected.',
            'database_error': 'Database error occurred. Please try again.',
            'db_file_exists': 'Database file with this name already exists.',
            'template_not_found': 'Template database (mahi.db) not found.',
            'user_has_planners': f'Cannot delete user. User is still associated with centers: {query_params.get("centers", "")}. Please remove all planner associations first.',
            'center_has_planners': f'Cannot delete center. Center is still associated with users: {query_params.get("users", "")}. Please remove all planner associations first.',
            'last_planner_for_center': f'Cannot delete planner. This is the last planner for center "{query_params.get("center", "")}". Each center must have at least one planner.'
        }
        message = error_messages.get(query_params['error'], 'An error occurred.')
        message_div = Div(P(message), style="color: #f8d7da; background: #842029; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #dc3545; font-weight: 500;")

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
        message_div,
        show_users(),
        show_centers(),
        show_planners(),
        cls="container",
    )
# ~/~ end
# ~/~ end
# ~/~ begin <<docs/gong-program/admin-change.md#admin-change-md>>[init]

# ~/~ begin <<docs/gong-program/admin-change.md#change-users>>[init]

@rt('/delete_user/{email}')
def delete_user(session, email: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    try:
        # Check if user has any planner associations
        user_planners = planners("user_email = ?", (email,))
        if user_planners:
            # Get the center names for the error message
            center_names = [p.center_name for p in user_planners]
            centers_list = ", ".join(center_names)
            return RedirectResponse(f'/admin_page?error=user_has_planners&centers={centers_list}')

        # If no planner associations, proceed with deletion
        db.execute("DELETE FROM users WHERE email = ?", (email,))
        return RedirectResponse('/admin_page?success=user_deleted')
    except Exception as e:
        return Main(
            Nav(Li(A("Admin", href="/admin_page"))),
            Div(H1("Error"), P(f"Could not delete user: {str(e)}")),
            cls="container"
        )

@rt('/add_user')
def add_user(session, new_user_email: str, role_name: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    if not new_user_email or not role_name:
        return RedirectResponse('/admin_page?error=missing_fields')

    try:
        # Check if user already exists
        existing_user = users("email = ?", (new_user_email,))
        if existing_user:
            return RedirectResponse('/admin_page?error=user_exists')

        # Validate role
        if role_name not in ['admin', 'user']:
            return RedirectResponse('/admin_page?error=invalid_role')

        # Add new user
        users.insert(
            email=new_user_email,
            name=new_user_email.split('@')[0],  # Use email prefix as default name
            role_name=role_name,
            is_active=False,
            magic_link_token=None,
            magic_link_expiry=None
        )
        return RedirectResponse('/admin_page?success=user_added')
    except Exception as e:
        return RedirectResponse('/admin_page?error=database_error')
# ~/~ end
# ~/~ begin <<docs/gong-program/admin-change.md#change-centers>>[init]

@rt('/delete_center/{center_name}')
def delete_center(session, center_name: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    try:
        # Get the center info to find the database file
        center_info = centers("center_name = ?", (center_name,))
        if not center_info:
            return RedirectResponse('/admin_page?error=center_not_found')

        # Check if center has any planner associations
        center_planners = planners("center_name = ?", (center_name,))
        if center_planners:
            # Get the user emails for the error message
            user_emails = [p.user_email for p in center_planners]
            users_list = ", ".join(user_emails)
            return RedirectResponse(f'/admin_page?error=center_has_planners&users={users_list}')

        gong_db_name = center_info[0].gong_db_name
        db_path = f'data/{gong_db_name}'

        # If no planner associations, proceed with deletion
        db.execute("DELETE FROM centers WHERE center_name = ?", (center_name,))

        # Finally, delete the associated database file if it exists
        if os.path.exists(db_path):
            os.remove(db_path)
            # Also remove any SQLite journal files
            for ext in ['-shm', '-wal']:
                journal_file = db_path + ext
                if os.path.exists(journal_file):
                    os.remove(journal_file)

        return RedirectResponse('/admin_page?success=center_deleted')
    except Exception as e:
        return Main(
            Nav(Li(A("Admin", href="/admin_page"))),
            Div(H1("Error"), P(f"Could not delete center: {str(e)}")),
            cls="container"
        )

@rt('/add_center')
def add_center(session, new_center_name: str, new_gong_db_name: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    if not new_center_name or not new_gong_db_name:
        return RedirectResponse('/admin_page?error=missing_fields')

    try:
        # Check if center already exists
        existing_center = centers("center_name = ?", (new_center_name,))
        if existing_center:
            return RedirectResponse('/admin_page?error=center_exists')

        # Ensure gong_db_name ends with .db
        if not new_gong_db_name.endswith('.db'):
            new_gong_db_name += '.db'

        # Check if database file already exists
        db_path = f'data/{new_gong_db_name}'
        if os.path.exists(db_path):
            return RedirectResponse('/admin_page?error=db_file_exists')

        # Copy mahi.db as template for new center
        template_db = 'data/mahi.db'
        if not os.path.exists(template_db):
            return RedirectResponse('/admin_page?error=template_not_found')

        # Create the new database by copying mahi.db
        shutil.copy2(template_db, db_path)

        # Add new center to the centers table
        centers.insert(
            center_name=new_center_name,
            gong_db_name=new_gong_db_name
        )
        return RedirectResponse('/admin_page?success=center_added')
    except Exception as e:
        return RedirectResponse('/admin_page?error=database_error')
# ~/~ end
# ~/~ begin <<docs/gong-program/admin-change.md#change-planners>>[init]

@rt('/delete_planner/{user_email}/{center_name}')
def delete_planner(session, user_email: str, center_name: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    try:
        # Check how many planners are associated with this center
        center_planners = planners("center_name = ?", (center_name,))

        # If this is the only planner for this center, prevent deletion
        if len(center_planners) <= 1:
            return RedirectResponse(f'/admin_page?error=last_planner_for_center&center={center_name}')

        # If there are other planners for this center, proceed with deletion
        db.execute("DELETE FROM planners WHERE user_email = ? AND center_name = ?", (user_email, center_name))
        return RedirectResponse('/admin_page?success=planner_deleted')
    except Exception as e:
        return Main(
            Nav(Li(A("Admin", href="/admin_page"))),
            Div(H1("Error"), P(f"Could not delete planner association: {str(e)}")),
            cls="container"
        )

@rt('/add_planner')
def add_planner(session, new_planner_user_email: str, new_planner_center_name: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    if not new_planner_user_email or not new_planner_center_name:
        return RedirectResponse('/admin_page?error=missing_fields')

    try:
        # Check if user exists
        user_exists = users("email = ?", (new_planner_user_email,))
        if not user_exists:
            return RedirectResponse('/admin_page?error=user_not_found')

        # Check if center exists
        center_exists = centers("center_name = ?", (new_planner_center_name,))
        if not center_exists:
            return RedirectResponse('/admin_page?error=center_not_found')

        # Check if planner association already exists
        existing_planner = planners("user_email = ? AND center_name = ?", (new_planner_user_email, new_planner_center_name))
        if existing_planner:
            return RedirectResponse('/admin_page?error=planner_exists')

        # Add new planner association
        planners.insert(
            user_email=new_planner_user_email,
            center_name=new_planner_center_name
        )
        return RedirectResponse('/admin_page?success=planner_added')
    except Exception as e:
        return RedirectResponse('/admin_page?error=database_error')
# ~/~ end
# ~/~ end
# client = TestClient(app)
# print(client.get("/login").text)

serve()
# ~/~ end
