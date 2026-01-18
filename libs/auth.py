# ~/~ begin <<docs/gong-web-app/authenticate.md#libs/auth.py>>[init]
import os
import socket
import secrets
from datetime import datetime, timedelta
from functools import wraps
from fasthtml.common import *
from libs.utils import isa_dev_computer, send_email, feedback_to_user

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

"""
@rt('/login')
def get():   
    return auth.login()
"""    
def login():
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
"""
@rt('/create_magic_link')
def post(email: str):
    return auth.create_link(email, users)
"""
def create_link(email,users):
    if not email:
       return (feedback_to_user({'error': 'missing_email'}))

    magic_link_token = secrets.token_urlsafe(32)
    magic_link_expiry = datetime.now() + timedelta(minutes=15)
    try:
       user = users[email]
       users.update(email= email, magic_link_token= magic_link_token, magic_link_expiry= magic_link_expiry, number_link_touched= 0)
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

    magic_link = f"{base_url}/check_click_from_browser/{magic_link_token}"
    send_magic_link_email(email, magic_link)

    return P(feedback_to_user({'success': 'magic_link_sent'}), id="success"),
    HttpHeader('HX-Reswap', 'outerHTML'), Button("Magic link sent", type="submit", id="submit-btn", disabled=True, hx_swap_oob="true")
# ~/~ end
# ~/~ begin <<docs/gong-web-app/authenticate.md#send-link>>[init]

def send_magic_link_email(email_address: str, magic_link: str):

   email_subject = "Sign in to The App"
   email_text = f"""
   Hey there,

   Click this link to sign in to the Gong App: {magic_link}

   If you didn't request this, just ignore this email.

   With Metta
   The Gong App Team
   """
   if False: #isa_dev_computer():
       print(f'To: {email_address}\n Subject: {email_subject}\n\n{email_text}')
   else:
       send_email(email_subject, email_text, [email_address])
# ~/~ end
# ~/~ begin <<docs/gong-web-app/authenticate.md#verify-link>>[init]

def check_click_from_browser(request, token):
    if request.method == "GET":
        headers = dict(request.headers)
        sec_fetch_site = headers["sec-fetch-site"]
        print(f"link visited with GET + sec-fetch-site: {sec_fetch_site}")
        return Title("Human verification"), Main(
            P("Click below to proceed (bots can't do this):"),
            Button("✅ Yes, I'm human - Continue", 
                onclick="humanProceed()",
                style="font-size: 18px; padding: 12px;"),
            Script(f"""
                let clickCount = 0;
                function humanProceed() {{
                    clickCount++;
                    if (clickCount === 1) {{
                        // First click: show confirmation
                        document.querySelector('p').innerHTML = 'Great! One more click to verify.';
                        return;
                    }}
                    // Second deliberate click: proceed
                    window.location.href = '/authenticate_link/{token}';
                }} """ 
            ),
            cls="container")
    else:
        print("ignoring non GET (HEAD) html method")
        return "ignoring non GET html method"

def authenticate_link(session, token, users):
    nowstr = f"'{datetime.now()}'"
    try:
        user = users("magic_link_token = ? AND magic_link_expiry > ?", (token, nowstr))[0]
        usermail = user.email
        session['auth'] = usermail
        session['role'] = user.role_name
        users.update(email= user.email, magic_link_token= None, magic_link_expiry= None, is_active= True)
        print(f"{usermail} just got connected")
        return RedirectResponse('/dashboard')
    except IndexError:
        print("Invalid or expired magic link")
        return "Invalid or expired magic link"
# ~/~ end
# ~/~ begin <<docs/gong-web-app/authenticate.md#admin_required>>[init]

def admin_required(handler):
    @wraps(handler)
    def wrapper(session, *args, **kwargs):
        role = session['role']
        if not role or not role == "admin":
            # Redirect to unauthorized page if not admin
            return RedirectResponse('/no_access_right')
        # Proceed if user is admin
        return handler(session, *args, **kwargs)
    return wrapper
# ~/~ end
# ~/~ begin <<docs/gong-web-app/authentipass.md#admin_required>>[0]

def admin_required(handler):
    @wraps(handler)
    def wrapper(session, *args, **kwargs):
        role = session['role']
        if not role or not role == "admin":
            # Redirect to unauthorized page if not admin
            return RedirectResponse('/no_access_right')
        # Proceed if user is admin
        return handler(session, *args, **kwargs)
    return wrapper
# ~/~ end
# ~/~ end
