# Program start 

### Main program

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
<<user-feedback>>
# is user-feedback.md
<<utilities>>
# is utilities.md
<<authentication>>
# is authenticate.md
<<user-dashboard>>
# is dashboard.md
<<admin-show>>
# is admin-show.md
<<admin-change>>
# is admin-change.md

<<home-page>>

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
