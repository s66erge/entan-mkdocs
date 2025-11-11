# ~/~ begin <<docs/gong-web-app/0-gong-prog.md#main.py>>[init]

import secrets
import os
import socket
import markdown2
import smtplib
import shutil
import resend
from functools import wraps
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from fasthtml.common import *
# from starlette.testclient import TestClient

css = Style(':root {--pico-font-size: 95% ; --pico-font-family: Pacifico, cursive;}')

# ~/~ begin <<docs/gong-web-app/authenticate.md#auth-beforeware>>[init]

login_redir = RedirectResponse('/login', status_code=303)

def before(req, session):
   auth = req.scope['auth'] = session.get('auth', None)
   if not auth: return login_redir

bware = Beforeware(before, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', '/login','/', '/create_magic_link', r'/verify_magic_link/.*'])
# ~/~ end
# ~/~ begin <<docs/gong-web-app/authenticate.md#guard-role-admin>>[init]

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
# ~/~ end
# both in authenticate.md

app, rt = fast_app(live=True, debug=True, before=bware,hdrs=(picolink,css), title="Gong Users", favicon="favicon.ico")

# ~/~ begin <<docs/gong-web-app/database-setup.md#database-setup-md>>[init]

# ~/~ begin <<docs/gong-web-app/database-setup.md#setup-database>>[init]

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
# ~/~ begin <<docs/gong-web-app/database-setup.md#initialize-database>>[init]

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
# ~/~ end
# ~/~ begin <<docs/gong-web-app/user-feedback.md#user-feedback-md>>[init]

# ~/~ begin <<docs/gong-web-app/user-feedback.md#feedback-messages>>[init]

def feedback_to_user(params):
    # query_params = dict(request.query_params)
    # Handle success and error messages
    success_messages = {
        'magic_link_sent': "A link to sign in has been sent to your email. Please check your inbox. The link will expire in 15 minutes.",
        'user_added': 'User added successfully!',
        'center_added': 'Center added successfully!',
        'planner_added': 'Planner association added successfully!',
        'user_deleted': 'User deleted successfully!',
        'center_deleted': 'Center and associated database deleted successfully!',
        'planner_deleted': 'Planner association deleted successfully!'
    }
    error_messages = {
        'missing_email':'Email is required.',
        'not_registered':f'Email "{params.get("email", "")}" is not registered, try again or send a message to xxx@xxx.xx to get registered',
        'missing_fields': 'Please fill in all required fields.',
        'user_exists': 'User with this email already exists.',
        'center_exists': 'Center with this name already exists.',
        'planner_exists': 'This planner association already exists.',
        'user_not_found': 'User not found.',
        'center_not_found': 'Center not found.',
        'invalid_role': 'Invalid role selected.',
        'db_error': f'Database error occurred: {params.get("etext")}. Please contact the program support.',
        'db_file_exists': 'Database file with this name already exists.',
        'template_not_found': 'Template database (mahi.db) not found.',
        'user_has_planners': f'Cannot delete user. User is still associated with centers: {params.get("centers", "")}. Please remove all planner associations first.',
        'center_has_planners': f'Cannot delete center. Center is still associated with users: {params.get("users", "")}. Please remove all planner associations first.',
        'last_planner_for_center': f'Cannot delete planner. This is the last planner for center "{params.get("center", "")}". Each center must have at least one planner.'
    }
    message_div = None
    if 'success' in params:
        message = success_messages.get(params['success'], 'Operation completed successfully!')
        message_div = Div(
            Div(P(message), style="color: #d1f2d1; background: #0f5132; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #198754; font-weight: 500;"),
            Small("To clear this message and/or update the tables, reload the page")
        )
    elif 'error' in params:
        message = error_messages.get(params['error'], 'An error occurred.')
        message_div = Div(
            Div(P(message), style="color: #f8d7da; background: #842029; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #dc3545; font-weight: 500;"),
            Small("To clear this message, reload the page")
        )
    return message_div
# ~/~ end
# ~/~ begin <<docs/gong-web-app/user-feedback.md#db-error>>[init]

@rt('/db_error')
def db_error(session, etext: str):
    return Html(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Head(Title("Database error")),
        Body(Div(feedback_to_user({'error': 'db_error', 'etext': f'{etext}'}))),
        (A("Dashboard", href="/dashboard")),
        cls="container"
    )
# ~/~ end
# ~/~ end
# ~/~ begin <<docs/gong-web-app/utilities.md#utilities-md>>[init]
# ~/~ begin <<docs/gong-web-app/utilities.md#isa-dev-computer>>[init]

DEV_COMPUTERS = ["ASROCK-MY-OFFICE","DESKTOP-UIPS8J2","serge-virtual-linuxmint","serge-framework"]
def isa_dev_computer():
    hostname = socket.gethostname()
    return hostname in DEV_COMPUTERS
# ~/~ end
# ~/~ begin <<docs/gong-web-app/utilities.md#send-email>>[init]

def send_email(subject, body, recipients):
    # old code via smtp
    """
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
    """
    # using resend
    sender = "spegoff@authentica.eu" 
    resend.api_key = os.environ['RESEND_API_KEY']
    params: resend.Emails.SendParams = {
        "from": sender,
        "to": recipients,
        "subject": subject,
        "text": body,
    }

    email = resend.Emails.send(params)
    print(f'Message sent: {email}')
# ~/~ end
# ~/~ begin <<docs/gong-web-app/utilities.md#display-markdown>>[init]

def display_markdown(file_name:str):
    with open(f'md-text/{file_name}.md', "r") as f:
        html_content = markdown2.markdown(f.read())
    return NotStr(html_content)
# ~/~ end
# ~/~ begin <<docs/gong-web-app/utilities.md#not-implemented>>[init]
@rt('/unfinished')
def unfinished():
    return Main(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Div(H1("This feature is not yet implemented.")),
        cls="container"
    )
# ~/~ end
# ~/~ end
# ~/~ begin <<docs/gong-web-app/authenticate.md#authenticate-md>>[init]

# ~/~ begin <<docs/gong-web-app/authenticate.md#build-serve-login-form>>[init]
def signin_form():
   return Form(
       Div(
           Div(
               Input(id='email', type='email', placeholder='foo@bar.com'),
           ),
       ),
       Button("Sign In with Email", type="submit", id="submit-btn"),
       hx_post="/create_magic_link",
       hx_target="#error",
       hx_disabled_elt="#submit-btn"
   )

@rt('/login')
def get():   
   return Main(
       Div(
           H1("Sign In"),
           P("Enter your email to sign in to The App."),
           Div(signin_form(), id='login_form'),
           P(id="error")
       ), cls="container"
   )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/authenticate.md#handling-form>>[init]

@rt('/create_magic_link')
def post(email: str):
    if not email:
       return (feedback_to_user({'error': 'missing_email'}))

    magic_link_token = secrets.token_urlsafe(32)
    magic_link_expiry = datetime.now() + timedelta(minutes=15)
    try:
       user = users[email]
       users.update(email= email, magic_link_token= magic_link_token, magic_link_expiry= magic_link_expiry)
    except NotFoundError:
        return Div(
            (feedback_to_user({'error': 'not_registered', 'email': f"{email}"})),
            Div(signin_form(), hx_swap_oob="true", id="login_form")
        )
    
    domainame = os.environ.get('RAILWAY_PUBLIC_DOMAIN', None)

    if (not isa_dev_computer()) and (domainame is not None):
        base_url = 'https://' + os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    else: 
        print(" machine name: " + socket.gethostname())
        base_url = 'http://localhost:5001'

    magic_link = f"{base_url}/verify_magic_link/{magic_link_token}"
    send_magic_link_email(email, magic_link)

    return P(feedback_to_user({'success': 'magic_link_sent'}), id="success"),
    HttpHeader('HX-Reswap', 'outerHTML'), Button("Magic link sent", type="submit", id="submit-btn", disabled=True, hx_swap_oob="true")
# ~/~ end
# ~/~ begin <<docs/gong-web-app/authenticate.md#send-link>>[init]

def send_magic_link_email(email_address: str, magic_link: str):

   email_subject = "Sign in to The App"
   email_text = f"""
   Hey there,

   Click this link to sign in to The App: {magic_link}

   If you didn't request this, just ignore this email.

   Cheers,
   The App Team
   """
   resend_api_key = os.environ.get('RESEND_API_KEY','None')
   if resend_api_key == 'None':
       print(f'To: {email_address}\n Subject: {email_subject}\n\n{email_text}')
   else:
       send_email(email_subject, email_text, [email_address])
# ~/~ end
# ~/~ begin <<docs/gong-web-app/authenticate.md#verify-token>>[init]

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
# ~/~ begin <<docs/gong-web-app/authenticate.md#guard-role-admin>>[init]

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
# ~/~ end
# ~/~ begin <<docs/gong-web-app/authenticate.md#logout>>[init]
@rt('/logout')
def post(session):
    del session['auth']
    return HttpHeader('HX-Redirect', '/login')
# ~/~ end
# ~/~ end
# ~/~ begin <<docs/gong-web-app/dashboard.md#dashboard-md>>[init]

# ~/~ begin <<docs/gong-web-app/dashboard.md#dashboard>>[init]

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
# ~/~ end
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-show.md#admin-show-md>>[init]

# ~/~ begin <<docs/gong-web-app/admin-show.md#show-users>>[init]

def show_users_table():
    return Main(
        Table(
            Thead(
                Tr(Th("Email"), Th("Name"), Th("Role"), Th("Active"), Th("Action"))
            ),
            Tbody(
                *[Tr(
                    Td(u.email), 
                    Td(u.name or ""), 
                    Td(u.role_name), 
                    Td("Yes" if u.is_active else "No"),
                    Td(A("Delete", hx_post=f"/delete_user/{u.email}", hx_target="#users-feedback", hx_confirm="Are you sure you want to delete this user?"))
                ) for u in sorted(users(), key=lambda x: x.name)]
            )
        )
    )


def show_users_form():
    role_names = [r.role_name for r in roles()]
    return Main(
        Div(
            Form(
                Input(type="email", placeholder="User Email", name="new_user_email", required=True),
                Input(type="text", placeholder="User full name", name="name", required=True),                
                Select( 
                    Option("Select Role", value="", selected=True, disabled=True),
                    *[Option(role, value=role) for role in role_names],
                        name="role_name", required=True),
                Button("Add User", type="submit"), hx_post="/add_user",hx_target="#users-feedback"
            )
        )    
    )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-show.md#show-centers>>[init]

def show_centers_table():
    return Main(
        Table(
            Thead(
                Tr(Th("Center Name"), Th("Gong DB Name"), Th("Actions"))
            ),
            Tbody(
                *[Tr(
                    Td(c.center_name), 
                    Td(c.gong_db_name), 
                    Td(A("Delete", hx_post=f"/delete_center/{c.center_name}", hx_target="#centers-feedback", hx_confirm="Are you sure you want to delete this center?"))
                ) for c in sorted(centers(), key=lambda x: x.center_name)]
            )
        )
    )

def show_centers_form():
    return Main(
        Div(
            Form(
                Input(type="text", placeholder="Center Name", name="new_center_name", required=True),
                Input(type="text", placeholder="Gong DB Name (without .db)", name="new_gong_db_name", required=True),
                Small("The database file will be created as a copy of mahi.db"),
                Button("Add Center", type="submit"), hx_post="/add_center",hx_target="#centers-feedback"
            )
        )
    )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-show.md#show-planners>>[init]

def show_planners_table():
    return Main(
        Table(
            Thead(
                Tr(Th("User Email"), Th("Center Name"), Th("Actions"))
            ),
            Tbody(
                *[Tr(
                    Td(p.user_email), 
                    Td(p.center_name), 
                    Td(A("Delete", hx_post=f"/delete_planner/{p.user_email}/{p.center_name}", hx_target="#planners-feedback", hx_confirm='Are you sure you want to delete this planner association?'))
                ) for p in sorted(planners(), key=lambda x: x.center_name)]
            )
        )
    )

def show_planners_form():
    sorted_centers = sorted(centers(), key=lambda x: x.center_name)
    sorted_users = sorted(users(), key=lambda x: x.name)
    return Main(
        Div(
            Form(
                Select(
                    Option("Select User", value="", selected=True, disabled=True),
                    *[Option(u.email, value=u.email) for u in sorted_users],
                    name="new_planner_user_email", required=True
                ),
                Select(
                    Option("Select Center", value="", selected=True, disabled=True),
                    *[Option(c.center_name, value=c.center_name) for c in sorted_centers],
                    name="new_planner_center_name", required=True
                ),
                Button("Add Planner", type="submit"), hx_post="/add_planner", hx_target="#planners-feedback"
            )
        )
    )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-show.md#admin-page>>[init]

@rt('/admin_page')
@admin_required
def admin(session, request):
    params = dict(request.query_params)
    return Main(
        Nav(
            Ul(
                Li(A("Dashboard", href="/dashboard")),
                Li(A("Contact", href="#")),
                Li(A("About", href="#")),
            ), 
            Button("Logout", hx_post="/logout"),
        ),
        Div(display_markdown("admin-show")),
        feedback_to_user(params),

        H2("Users"),
        Div(feedback_to_user(params), id="users-feedback"),
        Div(show_users_table(), id="users-table"),
        H4("Add New User"),
        Div(show_users_form(), id="users-form"),

        H2("Centers"),
        Div(feedback_to_user(params), id="centers-feedback"),
        Div(show_centers_table(), id="centers-table"),
        H4("Add New Center"),
        Div(show_centers_form(), id="centers-form"),

        # show_planners(),
        H2("Planners"),
        Div(feedback_to_user(params), id="planners-feedback"),
        Div(show_planners_table(), id="planners-table"),
        H4("Add New Planner"),
        Div(show_planners_form(), id="planners-form"),

        cls="container",
    )
# ~/~ end
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-change.md#admin-change-md>>[init]
# ~/~ begin <<docs/gong-web-app/admin-change.md#delete-user>>[init]

@rt('/delete_user/{email}')
@admin_required
def post(session, email: str):
    try:
        user_info = users("email = ?",(email,))
        user_planners = planners("user_email = ?", (email,))  ## [1]

        if not user_info:
            message = {'error' : 'user_not_found'}

        elif user_planners:  ## [1] 
            center_names = [p.center_name for p in user_planners]  ## [2]
            centers_list = ", ".join(center_names)
            message = {"error": "user_has_planners", "centers": f"{centers_list}"}

        else:  ## [3]
            db.execute("DELETE FROM users WHERE email = ?", (email,))
            message = {"success": "user_deleted"}

        return Div(
            Div(feedback_to_user(message)),
            Div(show_users_table(), hx_swap_oob="true", id="users-table") if "success" in message else None,
            ## [4]
            Div(show_planners_form(), hx_swap_oob="true", id="planners-form") if "success" in message else None
        )
    except Exception as e:
        return Redirect(f'/db_error?etext={e}')
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-change.md#add-user>>[init]
@rt('/add_user')
@admin_required
def post(session, new_user_email: str = "", name: str = "",role_name: str =""):
    try:
        if new_user_email == "" or name == "" or role_name == "":
            message = {"error" : "missing_fields"}

        elif not roles("role_name = ?", (role_name,)):
            message = {"error": "invalid_role"}

        elif users("email = ?", (new_user_email,)):
            message = {"error": "user_exists"}

        else:  ## [1]
            users.insert(
            email=new_user_email,
            name=name,
            role_name=role_name,
            is_active=False,
            magic_link_token=None,
            magic_link_expiry=None
            )
            message = {"success": "user_added"}

        return Div(
            Div(feedback_to_user(message)),
            Div(show_users_table(), hx_swap_oob="true", id="users-table") if "success" in message else None,
            Div(show_users_form(), hx_swap_oob="true", id="users-form"),
            ## [2]
            Div(show_planners_form(), hx_swap_oob="true", id="planners-form") if "success" in message else None
        )
    except Exception as e:
        return Redirect(f'/db_error?etext={e}')
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-change.md#delete-center>>[init]

@rt('/delete_center/{center_name}')
@admin_required
def post(session, center_name: str):
    try:
        center_info = centers("center_name = ?", (center_name,))
        gong_db_name = center_info[0].gong_db_name  ## [1]
        db_path = f'data/{gong_db_name}'  ## [1]
        center_planners = planners("center_name = ?", (center_name,))  ## [2]

        if not center_info:
            message = {'error' : 'center_not_found'}

        elif center_planners:  ## [2]
            user_emails = [p.user_email for p in center_planners]  ## [3]
            users_list = ", ".join(user_emails)
            message = {'error' : 'center_has_planners','users' : f'{users_list}'}

        else:  ## [4]
            db.execute("DELETE FROM centers WHERE center_name = ?", (center_name,))
            if os.path.exists(db_path):
                os.remove(db_path)
                for ext in ['-shm', '-wal']:  ## [5]
                    journal_file = db_path + ext
                    if os.path.exists(journal_file):
                        os.remove(journal_file)
            message = {'success' : 'center_deleted'}

        return Div(
            Div(feedback_to_user(message)),
            Div(show_centers_table(), hx_swap_oob="true", id="centers-table") if "success" in message else None,
            ## [6]
            Div(show_planners_form(), hx_swap_oob="true", id="planners-form") if "success" in message else None
        )
    except Exception as e:
        return Redirect(f'/db_error?etext={e}')
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-change.md#add-center>>[init]

@rt('/add_center')
@admin_required
def post(session, new_center_name: str = "", new_gong_db_name: str = ""):
    ## [1]
    if not new_gong_db_name.endswith('.db'):
        new_gong_db_name += '.db'
    db_path = f'data/{new_gong_db_name}'
    template_db = 'data/mahi.db'

    try:
        if new_center_name == "" or new_gong_db_name == "":
            message = {"error" : "missing_fields"}

        elif centers("center_name = ?", (new_center_name,)):
            message = {"error" : "center_exists"}

        elif os.path.exists(db_path):
            message = {"error" : 'db_file_exists'}

        elif not os.path.exists(template_db):
            message = {'error' : 'template_not_found'}

        else:  ## [2]
            shutil.copy2(template_db, db_path)
            centers.insert(
                center_name=new_center_name,
                gong_db_name=new_gong_db_name
            )
            message = {'success': 'center_added'}

        return Div(
            Div(feedback_to_user(message)),
            Div(show_centers_table(), hx_swap_oob="true", id="centers-table") if "success" in message else None,
            Div(show_centers_form(), hx_swap_oob="true", id="centers-form"),
            ## [3]
            Div(show_planners_form(), hx_swap_oob="true", id="planners-form") if "success" in message else None
        )
    except Exception as e:
        return Redirect(f'/db_error?etext={e}')
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-change.md#delete-planner>>[init]

@rt('/delete_planner/{user_email}/{center_name}')
@admin_required
def post(session, user_email: str, center_name: str):
    try:
        center_planners = planners("center_name = ?", (center_name,))
        if len(center_planners) == 1:  ## [1]
            message ={"error" : "last_planner_for_center", "center" : f"{center_name}"}

        else:  ## [2]
            db.execute("DELETE FROM planners WHERE user_email = ? AND center_name = ?", (user_email, center_name))
            message = {"success" : "planner_deleted"}

        return Div(
            Div(feedback_to_user(message)),
            Div(show_planners_table(), hx_swap_oob="true", id="planners-table") if "success" in message else None
        )

    except Exception as e:
        return Redirect(f'/db_error?etext={e}')
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-change.md#add-planner>>[init]

@rt('/add_planner')
@admin_required
def post(session, new_planner_user_email: str = "", new_planner_center_name: str = ""):
    try:
        if new_planner_user_email == "" or new_planner_center_name == "":
            message = {"error" : "missing_fields"}

        elif not users("email = ?", (new_planner_user_email,)):
            message = {"error" : "user_not_found"}

        elif not centers("center_name = ?", (new_planner_center_name,)):
            message = {'error' : 'center_not_found'}

        elif planners("user_email = ? AND center_name = ?", (new_planner_user_email, new_planner_center_name)):
            message = {'error' : 'planner_exists'}

        else:  ## (1)
            planners.insert(
            user_email=new_planner_user_email,
            center_name=new_planner_center_name
            )
            message = {'success' : 'planner_added'}

        return Div(
            Div(feedback_to_user(message)),
            Div(show_planners_table(), hx_swap_oob="true", id="planners-table") if "success" in message else None,
            Div(show_planners_form(), hx_swap_oob="true", id="planners-form")
        )
    except Exception as e:
        return Redirect(f'/db_error?etext={e}')
# ~/~ end
# ~/~ end

# ~/~ begin <<docs/gong-web-app/0-gong-prog.md#home-page>>[init]
@rt('/')
def home():
    return Main(
        Div(display_markdown("home")),
        A("Login",href="/login", class_="button"),
        cls="container")
# ~/~ end

# client = TestClient(app)
# print(client.get("/login").text)

serve()
# ~/~ end
