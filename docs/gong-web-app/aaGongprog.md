# Program start 

### Main program

TODO decorator to check role in admin routes

TODO create special page for database errors

``` {.python file= main.py}

import secrets
import os
import socket
import markdown2
import smtplib
import shutil
from functools import wraps
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from fasthtml.common import *
# from starlette.testclient import TestClient

css = Style(':root {--pico-font-size: 95% ; --pico-font-family: Pacifico, cursive;}')

<<auth-beforeware>>
<<guard-role-admin>>
# in authenticate.md

app, rt = fast_app(live=True, debug=True, before=bware,hdrs=(picolink,css), title="Gong Users", favicon="favicon.ico")

<<database-setup>>
# is adatabase-setup.md
<<feedback-messages>>
<<database-error>>
<<utilities>>
# is utilities.md
<<authentication>>
# is authenticate.md
<<home-page>>
<<user-dashboard>>
# is dashboard.md
<<admin-show>>
# is admin-show.md
<<admin-change-md>>
# is admin-change.md

# client = TestClient(app)
# print(client.get("/login").text)

serve()
```
### Home page   


``` {.python #home-page}
@rt('/')
def home():
    return Main(
        Div(display_markdown("home")),
        A("Login",href="/login", class_="button"),
        cls="container")
```

``` {.python #feedback-messages}

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
```

``` {.python #database-error}
@rt('/db_error')
def db_error(session, etext: str):
    return Main(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Div(feedback_to_user({'error': 'db_error', 'etext': f'{etext}'})),
        cls="container"
    )

