# ~/~ begin <<docs/gong-web-app/authentipass.md#libs/authpass.py>>[init]

from functools import wraps
from passlib.context import CryptContext
from fasthtml.common import *
from libs.utils import isa_dev_computer, send_email, feedback_to_user

# ~/~ begin <<docs/gong-web-app/authentipass.md#register>>[init]
def MyForm(btn_text, target):
    return Form(
        Input(id="email", type="email", placeholder="Email", required=True),
        Input(id="password", type="password", placeholder="Password", required=True),
        Button(btn_text, type="submit"),
        Span(id="error", style="color:red"),
        hx_post=target,
        hx_target="#error",
    )

"""
@rt('/register')
def get():
    return authpass.register_get()
"""
def register_get():
    return Container(
        Article(
            H1("Register"),
            MyForm("Register", "/registercheck"),
            Hr(),
            P("Already have an account? ", A("Login", href="/login")),
            cls="mw-480 mx-auto"
        )
    )

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

"""
@rt('/registercheck')
def post(email:str, password:str):
    return authpass.register_post(email, password)
"""
def register_post(email, password, users):
    User = users.dataclass()
    try:
        users[email]
        return "User already exists"
    except NotFoundError:
        new_user = User(email=email, password=get_password_hash(password))
        users.insert(new_user)
        return HttpHeader('HX-Redirect', '/login')

"""
@rt('/login')
def get():
    return authpass.login_get()
"""
def login_get():
    return Container(
        Article(
            H1("Login"),
            MyForm("Login", target="/logincheck"),
            Hr(),
            # P("Want to create an Account? ", A("Register", href="/register")),
            cls="mw-480 mx-auto"
        )
    )

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

"""
@rt('/logincheck')
def post():
    return authpass.logincheck()
"""
def logincheck(session, email, password, users):
    try:
        user = users[email]
    except NotFoundError:
        return "Email or password are incorrect"
    if not verify_password(password, user.password):
        return "Email or password are incorrect"
    session['auth'] = user.email
    session['role'] = user.role_name
    return HttpHeader('HX-Redirect', '/dashboard')

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
