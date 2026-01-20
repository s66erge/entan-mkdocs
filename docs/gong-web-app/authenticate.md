# Authentication with a code by email

This is a passwordless authentication:

- The user enters their email on a website
- The website generates a random string (a "token") and saves it together with the user's email into a database
- The website sends an email to the user with the token
- The user enters the token into the website
- The website looks for a record in the users database table with the token
- If it can find a record, the user will be logged in (again by storing information in the session)

```{.python file=libs/auth.py}
import os
import socket
import secrets
import string
from datetime import datetime, timedelta
from functools import wraps
from fasthtml.common import *
from libs.utils import isa_dev_computer, send_email, feedback_to_user

<<build-serve-login-form>>
<<handling-form>>
<<send-link>>
<<verify-link>>
<<admin_required>>
```

### Login form

The actual form element is extracted into a MyForm() function. Its not really needed this time, since we don't use it a second time!

```{.python #build-serve-login-form}
def signin_form():
   return Form(
       Div(
           Div(
               Input(id='email', type='email', placeholder='foo@bar.com'),
           ),
       ),
       Button("Sign In with Email", type="submit", id="submit-btn"),
       hx_post="/create_code",
       hx_target="#signin-error",
       hx_disabled_elt="#submit-btn"
   )

def code_form():
    return Form(
        Div(
            Div(Input(id='code', name='code', type='text', placeholder='Enter your code')),
        ),
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
            P("Enter your email to sign in to The App."),
            Div(signin_form(), id='login_form'),
            P(id="signin-error"),
            Hr(),
            P("Already have a code? Enter it below."),
            Div(code_form(), id='code_form'),
            P(id="code-error"),    
        ), cls="container"
   )
```

### Handling the login form

This handler first checks if the email is present. If its not, it returns an error that will be swapped into the #error paragraph in the form by HTMX, just like last time.

We create a token using the secrets package from the python standard library. This token is a 6 characters long string. Also we generate an expiry date, which lies 15 minutes in the future.

Then it tries to find a user with the given email and if there is no user with this email, the IndexError is raised and it returns an error like above.

Then we update the user row in the database with the expiration date and the token itself.

Then we create the login code.

If everything went well, we return a success message to the user. Remember, the form has been defined to swap the content of the #error paragraph. Since I want to change the appearance of the text we send back, I also send back a HX-Reswap header with the value outerHTML. This tells HTMX to swap the outer HTML of the #error html element with the content we send back, a paragraph tag with the success message.

Also I want to disable the submit button and show a message that the magic link has been sent. To do this, we use one of the most powerful features of HTMX, out-of-band swaps. In HTMX you can update more than one piece of UI by setting the hx-swap-oob attribute to true on an element. HTMX will then swap in the returned element at the location of the element with the same id (#submit-btn in this case). You can read more about HTMX's out-of-band swaps [here](https://htmx.org/docs/#oob_swaps).

```{.python #handling-form}
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
    User = users.dataclass()
    login_code = _generate_login_code()  # e.g. "483921"
    magic_link_expiry = datetime.now() + timedelta(minutes=15)
    print(email, users[email])
    try:
       user = users[email]
       users.update(email= email, magic_link_token= login_code, magic_link_expiry= magic_link_expiry, number_link_touched= 0)
    except NotFoundError:
        return Div(
            (feedback_to_user({'error': 'not_registered', 'email': f"{email}"})),
            Div(signin_form(), hx_swap_oob="true", id="login_form")
        )
    send_login_code_email(email, login_code)
    return (
        P(feedback_to_user({'success': 'magic_link_sent'}), id="success"),
        HttpHeader('HX-Reswap', 'outerHTML'),
        Button("Code sent", type="submit", id="submit-btn",
               disabled=True, hx_swap_oob="true")
    )
    
```

### Send the code

Now we only need to send an email to the user with the code.

In production mode - remote or local within railway CLI -, we can use the smtplib via send_email (in utilities.md) to send an email using Gmail's SMTP server. 

In dev mode, lets just mock sending the email by printing the email content to the console.

```{.python #send-link}

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
```

### Authenticate the user

We save the current time into the variable now, because we need to look whether the token is already expired. Then we retrieve the first item with the specified token and an expiration date that lies in the future from the users table.

There should only be one or no user coming back from this query, so we wrap this whole code in a try/catch block.

If a user has been found using this query, we will save his or hers email in the auth key of our session dictionary. If its the first time the user logs in, we set is_active to true for this database record.

We do this to keep our database clean. Imagine a hacker enters thousands of random email addresses into our beautiful sign in form and therefore creates thousands of records in our database. To keep our database clean, we can use this is_active column to delete all inactive database records periodically using cron jobs.

```{.python #verify-link}

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
```

```{.python #admin_required}

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
```

