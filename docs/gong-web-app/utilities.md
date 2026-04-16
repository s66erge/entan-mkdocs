# Utilities

- checking if the program runs on a development machine
- sending an email
- displaying the content of a markdown file
- route or function not implemented yet


```python
#| file: libs/utils.py 

import socket
import tempfile
import calendar
import json
import pandas as pd
from zoneinfo import ZoneInfo
from fasthtml.common import *
import resend 
import markdown2
import os
from datetime import datetime, date, timedelta

class Skey: # session keys
    AUTH = "auth"
    ROLE = "role"
    CENTER = "center"
    PLANOK = "planOK"
    TIMESOK = "timesOK"
    SAVED_PLAN = "saved_plan"
    SAVED_TIMES = "saved_times"
    @classmethod
    def get(cls, name, default=None):
        return getattr(cls, name, default)

class Pkey: # parameters keys
    TIMEZON = "timezon"
    LOCATION = "location"
    GONG_ID = "gong_id"
    TARGETS = "targets"
    DEFAULT_PERIOD = "default_period"
    @classmethod
    def get(cls, name, default=None):
        return getattr(cls, name, default)

class Globals:
    INITIAL_COUNTDOWN = 4000 # seconds before auto-abandoning an edit session, set in planning_page and used in JS_CLIENT_TIMER
    SUBDIR_TEMP = "temp" # subdir of get_db_path() for temp files
    MONTHS_TO_FETCH = 12 # when fetching dhamma courses from dhamma.org, how many months to fetch starting from current month
    DAYS_TO_FETCH = 0 # when fetching dharma courses from dhamma.org, how many extra days to fetch after the last day of the last month (to catch late announcements)
    SHORT_DELAY = 3 # seconds: waiting time before uploading file to minio IN DEV MODE
    CENTER_BUCKET = "centers-data" # bucket name for local center data 
    PI_BUCKET = "dhamma-gong-databases"  # bucket name for db exchange with Rasperry Pis
    PI_FILE_JSON = "settings.json"  # file used for getting PI production date
    PI_FILE_KEY1 = "general"     # 1st key to find production date in PI_FILE_JSON
    PI_FILE_KEY2 = "db_version"  # 2nd key to find production date
    DEV_USER = "spegoff@authentica.eu" # IN PROD: can force state to free AND TEMPORALY SAVE CHANGES
    TEST_CENTER = "Testx" # used for testing in DEV mode
    @classmethod
    def get(cls, name, default=None):
        return getattr(cls, name, default)

<<isdev-computer>>
<<istest-db>>
<<send-email>>
<<display-markdown>>
<<plus-months-days>>

```

### Check if the current computer is a development machine

This function checks if the program runs on one of a predefined list of development machines. This is useful to determine whether to use a local or remote base URL for building the registation link.

```python
#| id: isdev-computer
def isa_dev_computer():
    DEV_COMPUTERS = ["serge-asrock","DESKTOP-UIPS8J2","serge-framework", "serge-bosgame", "Solaris" ]
    hostname = socket.gethostname()
    return hostname in DEV_COMPUTERS

def get_db_path():
    if isa_dev_computer():
        root = ""
    elif os.environ.get('Github_CI') == 'true': # Github CI actions
        root = ""
    else:   # Railway production permanent storage
        root = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH',"None") + "/"
    return root + "data/"

def dev_comp_or_user(session):
    return isa_dev_computer() or session[Skey.AUTH] == Globals.DEV_USER

```

### Check if current db is a teporary db in memory

```python
#| id: istest-db
def isa_db_test(db):
    return 'Database <apsw.Connection object ""' in str(db)
```


### Send email 

#### via Google smtp

We will need to create an App Password in your Google Account settings as we have 2-Step Verification enabled. And we set up environmemt variables 'GOOGLE_SMTP_USER' and 'GOOGLE_SMTP_PASS' .

#### via resend.com

As railway does not give smtp access to Hobby plan, we are using instead the resend API: https://resend.com/docs/send-with-python . And we set up [the environmemt variable 'RESEND_API_KEY'](../setup-deploy/railway.md#resend-api-key) .

### Example

Using: *send_email(subject, body, recipients)*

- subject = "Hello from Python"
- body = "This is a test email sent from Python."
- recipients = ["recipient1@gmail.com"]  : list of recipients 

```python
#| id: send-email

def send_email(subject, body, recipients):
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
    print(f'Message sent: {email} to {recipients}')
```

### Displaying the content of a markdown file

This function reads a markdown file name, without the extension '.md', then finds the file in the 'md-text' directory and converts it to HTML using the `markdown2` library, which is then returned as a NotStr object for rendering in the app.

```python
#| id: display-markdown

def display_markdown(file_name:str, insert=None):
    file_path = os.path.join('md-text', f"{file_name}.md")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
            if insert and "{{" in content and "}}" in content:
                new_content = content.split("{{", 1)[0] + insert + content.split("}}", 1)[1]
            else:
                new_content = content
            html_content = markdown2.markdown(new_content)
        return NotStr(html_content)
    else:
        return f"!!! NO markdown file {file_name}.md IN md-text folder !!!"
```

### Add months and days to an ISO date

Return an ISO date string num_months and num_days after date_str (YYYY-MM-DD).
Uses divmod to compute year/month rollover and preserves end-of-month.

```python
#| id: plus-months-days

def add_months_days(date_str, num_months, num_days):
    dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    # total months since year 0 (make month zero-based)
    total = dt.year * 12 + (dt.month - 1) + num_months
    new_year, new_month0 = divmod(total, 12)
    new_month = new_month0 + 1
    last_day = calendar.monthrange(new_year, new_month)[1]
    new_day = min(dt.day, last_day)
    result_date = date(new_year, new_month, new_day)
    # Add num_days to the result
    result_date += timedelta(days=num_days)
    return result_date.isoformat()

def short_iso(date_time: datetime, timezon="UTC"):
    return date_time.astimezone(ZoneInfo(timezon)).strftime('%Y-%m-%dT%H:%M:%S%z')

def seconds_to_hours_minutes(total_seconds):
    hours = total_seconds // 3600
    remaining_minutes = (total_seconds % 3600) // 60
    return hours, remaining_minutes

```
