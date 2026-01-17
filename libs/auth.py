# ~/~ begin <<docs/gong-web-app/authenticate.md#libs/auth.py>>[init]
import os
import socket
import secrets
from datetime import datetime, timedelta
from functools import wraps
from crawlerdetect import CrawlerDetect
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

   If you have a @dhamma.org address and clicking the long link does not connect you to the app, re-enter your email on the login screen and follow the instructions under the link.

   Click this link to sign in to The App: {magic_link}

   Instructions for ...@dhamma.org address when clicking the link does not work:
   1. copy the link fragment here below starting with 'ttps://entan...' until the last character on the same line
   2. paste into the address bar of a new tab in your browser - do not ENTER yet
   3. add the letter 'h' at the start of the link fragment, then ENTER
   {magic_link[1:]}

   If you didn't request this, just ignore this email.

   With Metta
   The App Team
   """
   if isa_dev_computer():
       print(f'To: {email_address}\n Subject: {email_subject}\n\n{email_text}')
   else:
       send_email(email_subject, email_text, [email_address])
# ~/~ end
# ~/~ begin <<docs/gong-web-app/authenticate.md#verify-link>>[init]
"""
@rt('/verify_magic_link/{token}')
def get(session, request, token: str):
    return auth.verify_link(session, request, token, users) 
"""
def is_bot_request(request):
    if request.method == 'HEAD':
        print("request.method = HEAD")
        return True
    # Full request context
    headers = dict(request.headers)
    headers['REQUEST_METHOD'] = request.method
    # cross-site request
    if headers.get('sec-fetch-site',"") == 'cross-site':
        print('cross-site request')
        return True
    # Primary detection
    crawler = CrawlerDetect(headers=headers) 
    if crawler.isCrawler():
        print(f"bot detected: {crawler.getMatches()}")
        return True
    # Additional Safe Links heuristics
    user_agent = request.headers.get('user-agent',"")
    if 'safelinks' in user_agent.lower():
        print("safelinks in User-Agent")
        return True
    return False


def magic_button(session, token, users):
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
        return "Invalid or expired magic link"

def verify_link(session, request, token, users):
    print(f"{request.method} {request.url}")
    print(request.headers)
    print(request.body)
    if is_bot_request(request):
        print("bot detected")  # UA + method checks
        return "Nothing"  # Bots + non-JS clients
        # Real user gets full landing page
    print("NOT a bot")
    return f"""
    <!DOCTYPE html>
    <html>
    <script>window.location.href='/magic_button/{token}'</script>
    <button onclick="window.location.href='/magic_button/{token}'">Sign In</button>
    </html>
    """

def verify_link2(session, request, token, users):
    nowstr = f"'{datetime.now()}'"
    try:
        if request.method == "GET":
            # cookie = dict(request.headers).get("cookie", "NO cookie")[0:9]
            # print(f"cookie: {cookie}")
            user = users("magic_link_token = ? AND magic_link_expiry > ?", (token, nowstr))[0]
            usermail = user.email
            num_get_link_touch = user.number_link_touched + 1
            users.update(email= user.email, number_link_touched= num_get_link_touch)
            session['auth'] = usermail
            session['role'] = user.role_name
            if (not usermail.endswith("dhamma.org") and num_get_link_touch == 1) or (usermail.endswith("dhamma.org") and num_get_link_touch >= 2):
            # if cookie == "session_=":
                users.update(email= user.email, magic_link_token= None, magic_link_expiry= None, is_active= True)
                print(f"{usermail} just got connected")
                return RedirectResponse('/dashboard')
            print("dhamma.org link cliqued first time")
            return "dhamma.org link cliqued first time"
        else:
            print("ignoring non GET (HEAD) html method")
            return "ignoring non GET html method"
    except IndexError:
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
# ~/~ end
