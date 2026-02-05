# ~/~ begin <<docs/gong-web-app/authenticate.md#libs/auth.py>>[init]
import os
import socket
import secrets
import string
from datetime import datetime, timedelta
from functools import wraps
from fasthtml.common import *
from libs.utils import isa_dev_computer, send_email, feedback_to_user

# ~/~ begin <<docs/gong-web-app/authenticate.md#build-serve-login-form>>[init]
def signin_form():
    return Form(
        Input(id='email', type='email', placeholder='foo@bar.com'),
        Button("Sign In with Email", type="submit", id="submit-btn"),
        hx_post="/create_code",
        hx_target="#signin-error",
        hx_disabled_elt="#submit-btn"
    )

def code_form():
    return Form(
        Input(id='code', name='code', type='text', placeholder='Enter your code'),
        Button("Verify code", type="submit", id="verify-btn"),
        hx_post="/verify_code",
        hx_target="#code-error",
        hx_disabled_elt="#verify-btn"
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
            P("Enter your email to sign in to the app."),
            Div(signin_form(), id='login_form'),
            P(id="signin-error"),
            Hr(style="background-color: white;height: 3px;"),
            Div(id='code_form'),
            P(id="code-error"),    
        ), cls="container"
   )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/authenticate.md#handling-form>>[init]
def _generate_login_code(length: int = 6) -> str:
    # e.g. 6-digit numeric code
    digits = string.digits
    return ''.join(secrets.choice(digits) for _ in range(length))

"""
@rt('/create_code')
def post(email: str):
    return auth.create_code(email, users)
"""

def create_code(email, users):
    if not email:
        return (feedback_to_user({'error': 'missing_email'}))

    login_code = _generate_login_code()  # e.g. "483921"
    magic_link_expiry = datetime.now() + timedelta(minutes=15)
    try:
        user_results = users("email = ?", (email,))[0]
        # If we get here, user exists
        users.update(
            email=email,
            magic_link_token=login_code,
            magic_link_expiry=magic_link_expiry,
            number_link_touched=0
        )
        send_login_code_email(email, login_code)
        return (
            P(feedback_to_user({'success': 'login_code_sent'}), id="success"),
            HttpHeader('HX-Reswap', 'outerHTML'),
            Button("Code sent", type="submit", id="submit-btn", disabled=True, hx_swap_oob="true"),
            Div(code_form(), id='code_form', hx_swap_oob="true")
        )
    except IndexError:
        # Handle case when no user is found
        return Div(
            feedback_to_user({'error': 'not_registered', 'email': f"{email}"}),
        )

# ~/~ end
# ~/~ begin <<docs/gong-web-app/authenticate.md#send-link>>[init]

def send_login_code_email(email_address: str, code: str):
    email_subject = "Your sign-in code for The App"
    email_text = f"""
Hey there,

Use this code to sign in to The Gong App:

    {code}

This code is valid for 15 minutes and can be used only once.

If you didn't request this, you can safely ignore this email.

With Metta
The Gong App Team
"""
    # dev toggle if you like
    if isa_dev_computer():
        print(f'To: {email_address}\nSubject: {email_subject}\n\n{email_text}')
    else:
        send_email(email_subject, email_text, [email_address])
# ~/~ end
# ~/~ begin <<docs/gong-web-app/authenticate.md#verify-link>>[init]

"""
@rt('/verify_code')
def post(code: str, session):
    return auth.verify_code(session, code, users)
"""
def verify_code(session, code, users):
    nowstr = f"'{datetime.now()}'"
    try:
        user = users("magic_link_token = ? AND magic_link_expiry > ?", (code, nowstr))[0]
    except IndexError:
        return feedback_to_user({'error': 'invalid_or_expired_code'})

    User = users.dataclass()
    usermail = user.email
    session['auth'] = usermail
    session['role'] = user.role_name


    users.update(
        email=user.email,
        magic_link_token=None,
        magic_link_expiry=None,
        is_active=True
    )
    print(f"{usermail} just got connected via code")
    #RedirectResponse('/dashboard', status_code=303)
    return Script("window.location.href = '/dashboard';")
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
