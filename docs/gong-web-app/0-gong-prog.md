# Gong main program 

### Program start



```{.python file=main.py}

import secrets
import os
import importlib
# import socket
# import markdown2
import smtplib
import shutil
import resend
from functools import wraps
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from fasthtml.common import *
# from starlette.testclient import TestClient

from libs import *

css = Style(':root {--pico-font-size: 95% ; --pico-font-family: Pacifico, cursive;}')

<<auth-beforeware>>
<<guard-role-admin>>
# both in authenticate.md

app, rt = fast_app(live=True, debug=True, title="Gong Users", favicon="favicon.ico",
                   before=bware, hdrs=(picolink,css),)

# <utilities-md>

<<database-setup-md>>
<<authenticate-md>>
<<dashboard-md>>
<<admin-show-md>>
<<admin-change-md>>

<<home-page>>

# client = TestClient(app)
# print(client.get("/login").text)

@rt('/unfinished')
def unfinished():
    return Main(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Div(H1("This feature is not yet implemented.")),
        cls="container"
    )

@rt('/db_error')
def db_error(session, etext: str):
    return Html(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Head(Title("Database error")),
        Body(Div(feedb.feedback_to_user({'error': 'db_error', 'etext': f'{etext}'}))),
        (A("Dashboard", href="/dashboard")),
        cls="container"
    )

serve()
```

### Home page   

```{.python #home-page}
@rt('/')
def home():
    return Main(
        Div(utils.display_markdown("home")),
        A("Login",href="/login", class_="button"),
        cls="container")
```
