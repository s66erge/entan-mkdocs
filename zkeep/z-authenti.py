# ~/~ begin <<docs/z-authenticate.md#src\z-authenticate.py>>[init]
from fasthtml.common import *
from starlette.testclient import TestClient
import secrets
from datetime import datetime, timedelta

frankenui = Link(rel='stylesheet', href='https://unpkg.com/franken-ui@1.1.0/dist/css/core.min.css')

tailwind = Script(src='https://cdn.tailwindcss.com')

# ~/~ begin <<docs/authenticate.md#beforeware>>[init]

login_redir = RedirectResponse('/login', status_code=303)

def before(req, session):
   auth = req.scope['auth'] = session.get('auth', None)
   if not auth: return login_redir

bware = Beforeware(before, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', '/login', '/send_magic_link', r'/verify_magic_link/.*'])
# ~/~ end
# ~/~ begin <<docs/z-authenticate.md#beforeware>>[0]

login_redir = RedirectResponse('/login', status_code=303)

def before(req, session):
   auth = req.scope['auth'] = session.get('auth', None)
   if not auth: return login_redir

bware = Beforeware(before, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', '/login', '/send_magic_link', r'/verify_magic_link/.*'])
# ~/~ end

app, rt = fast_app(live=True, debug=True, pico=False, hdrs=(frankenui, tailwind), before=bware)

# ~/~ begin <<docs/authenticate.md#setup-database>>[init]

db = database('data/virtualOW.db')

SQL_CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY NOT NULL,
    magic_link_token TEXT,
    magic_link_expiry TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE
); 
"""

db.execute(SQL_CREATE_USERS)   

users = db.t.users
User = users.dataclass()
# ~/~ end
# ~/~ begin <<docs/z-authenticate.md#setup-database>>[0]

db = database('data/virtualOW.db')

SQL_CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    email TEXT PRIMARY KEY NOT NULL,
    magic_link_token TEXT,
    magic_link_expiry TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE
);
"""

db.execute(SQL_CREATE_USERS)   

users = db.t.users
User = users.dataclass()
# ~/~ end
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
   return Div(
       Div(
           H1("Sign In"),
           P("Enter your email to sign in to The App."),
           MyForm("Sign In with Email", "/send_magic_link")
       )
   )
# ~/~ end
# ~/~ begin <<docs/z-authenticate.md#build-serve-login-form>>[0]
def MyForm(btn_text: str, target: str, cls: str = ""):
   return Form(
       Div(
           Div(
               Input(id='email', type='email', placeholder='foo@bar.com', cls='uk-input'),
               cls='uk-form-controls'
           ),
           cls='uk-margin'
       ),
       Button(btn_text, type="submit", cls="uk-button uk-button-primary w-full", id="submit-btn"),
       P(id="error", cls="uk-text-danger uk-text-small uk-text-italic uk-margin-top"),
       hx_post=target,
       hx_target="#error",
       hx_disabled_elt="#submit-btn",
       cls=f'uk-form-stacked {cls}'
   )

@rt('/login')
def get():   
   return Div(
       Div(
           H1("Sign In", cls="text-3xl font-bold tracking-tight uk-margin text-center"),
           P("Enter your email to sign in to The App.", cls="uk-text-muted uk-text-small text-center"),
           MyForm("Sign In with Email", "/send_magic_link", cls="uk-margin-top"),
           cls="uk-card uk-card-body"
       ),
       cls="uk-container max-w-[400px] uk-margin-top"
   )
# ~/~ end
# ~/~ begin <<docs/authenticate.md#handling-form>>[init]
@rt('/send_magic_link')
def post(email: str):
   if not email:
       return "Email is required"
   try:
       user = users[email]
   except NotFoundError:
       user = User(email=email, is_active=False, magic_link_token=None, magic_link_expiry=None)
       users.insert(user)

   magic_link_token = secrets.token_urlsafe(32)
   magic_link_expiry = datetime.now() + timedelta(minutes=15)

   users.update({'email': email, 'magic_link_token': magic_link_token, 'magic_link_expiry': magic_link_expiry})

   magic_link = f"http://localhost:5001/verify_magic_link/{magic_link_token}"

   send_magic_link_email(email, magic_link)

   return P("A link to sign in has been sent to your email. Please check your inbox. The link will expire in 15 minutes.", id="success"), HttpHeader('HX-Reswap', 'outerHTML'), Button("Magic link sent", type="submit", id="submit-btn", disabled=True, hx_swap_oob="true")
# ~/~ end
# ~/~ begin <<docs/z-authenticate.md#handling-form>>[0]
@rt('/send_magic_link')
def post(email: str):
   if not email:
       return "Email is required"
   try:
       user = users[email]
   except NotFoundError:
       user = User(email=email, is_active=False, magic_link_token=None, magic_link_expiry=None)
       users.insert(user)

   magic_link_token = secrets.token_urlsafe(32)
   magic_link_expiry = datetime.now() + timedelta(minutes=15)

   users.update({'email': email, 'magic_link_token': magic_link_token, 'magic_link_expiry': magic_link_expiry})

   magic_link = f"http://localhost:5001/verify_magic_link/{magic_link_token}"

   send_magic_link_email(email, magic_link)

   return P("A link to sign in has been sent to your email. Please check your inbox. The link will expire in 15 minutes.", id="success", cls="uk-margin-top uk-text-muted uk-text-small"), HttpHeader('HX-Reswap', 'outerHTML'), Button("Magic link sent", type="submit", cls="uk-button uk-button-primary w-full", id="submit-btn", disabled=True, hx_swap_oob="true")
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
# ~/~ begin <<docs/z-authenticate.md#send-link>>[0]
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
   now = datetime.now()
   try:
       user = users(where=f"magic_link_token = '{token}' AND magic_link_expiry > '{now}'")[0]
       session['auth'] = user.email
       users.update({'email': user.email, 'magic_link_token': None, 'magic_link_expiry': None, 'is_active': True})
       return RedirectResponse('/dashboard')
   except IndexError:
       return "Invalid or expired magic link"
# ~/~ end
# ~/~ begin <<docs/z-authenticate.md#verify-token>>[0]
@rt('/verify_magic_link/{token}')
def get(session, token: str):
   now = datetime.now()
   try:
       user = users(where=f"magic_link_token = '{token}' AND magic_link_expiry > '{now}'")[0]
       session['auth'] = user.email
       users.update({'email': user.email, 'magic_link_token': None, 'magic_link_expiry': None, 'is_active': True})
       return RedirectResponse('/dashboard')
   except IndexError:
       return "Invalid or expired magic link"
# ~/~ end
# ~/~ begin <<docs/authenticate.md#dashboard-page>>[init]
@rt('/logout')
def post(session):
   del session['auth']
   return HttpHeader('HX-Redirect', '/login')

@rt('/dashboard')
def get(session): 
   u = users[session['auth']]

   return Nav(
       Div(
           Ul(
               Li(
                   A("Dashboard",href='#')
               ),
               Li(
                   A("About",href='#'),
               ),
               Li(
                   A("Contact",href='#')
               ),
               cls='uk-navbar-nav'
           )
       ),
       Div(
           Div(
               Button(
                   "Logout",
                   hx_post='/logout'
               )
           )
       )
   ), Div(
       Div(
           H1("The dashboard"),
           P(f"You are logged in as '{user.email}'")
       )
   )
# ~/~ end
# ~/~ begin <<docs/z-authenticate.md#dashboard-page>>[0]
@rt('/logout')
def post(session):
   del session['auth']
   return HttpHeader('HX-Redirect', '/login')

@rt('/dashboard')
def get(session): 
   u = users[session['auth']]

   return Nav(
       Div(
           Ul(
               Li(
                   A("Dashboard",href='#'),
                   cls='uk-active'
               ),
               Li(
                   A("About",href='#'),
               ),
               Li(
                   A("Contact",href='#')
               ),
               cls='uk-navbar-nav'
           ),
           cls='uk-navbar-left'
       ),
       Div(
           Div(
               Button(
                   "Logout",
                   cls='uk-button uk-button-primary',
                   hx_post='/logout'
               ),
               cls="uk-navbar-item"
           ),
           cls='uk-navbar-right'
       ),
       uk_navbar=True,
       cls='uk-navbar uk-navbar-container px-4'
   ), Div(
       Div(
           H1("Dashboard", cls="text-3xl font-bold tracking-tight uk-margin text-center"),
           P(f"You are logged in as '{u.email}'"),
           cls="uk-card uk-card-body"
       ),
       cls="uk-container uk-margin-top"
   )
# ~/~ end

# client = TestClient(app)
# print(client.get("/login").text)

serve()
# ~/~ end
