# ~/~ begin <<docs/gong-web-app-code/utilities.md#libs/utils.py>>[init]

import socket
from dotenv import load_dotenv
from pathlib import Path
import calendar
from zoneinfo import ZoneInfo
from fasthtml.common import *
from dataclasses import dataclass
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

class Pkey: # parameters keys in excel sheet
    TIMEZON = "timezon"
    LOCATION = "location"
    GONG_ID = "gong_id"
    TARGETS = "targets"
    DEFAULT_PERIOD = "default_period"
    @classmethod
    def get(cls, name, default=None):
        return getattr(cls, name, default)

@dataclass(frozen=True)
class GlobalsDefinition:
    EMAIL_SENDER:str = "spegoff@authentica.eu"
    DEV_COMPUTERS = ["serge-bosgame", "serge-asrock", "serge-framework"]
    HTML_TAGS_CENTERS = {"F": "Fixed", "V": "Variable", "X": "Default - Variable"}
    MEDIA_TYPES = {".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                   ".db": "application/octet-stream"}
    ORANGE:str = "darkorange"
    INITIAL_COUNTDOWN:int = 4000 # seconds before auto-abandoning an edit session, set in planning_page and used in JS_CLIENT_TIMER
    SUBDIR_TEMP:str = "temp" # subdir of get_db_path() for temp files
    MONTHS_TO_FETCH:int = 12 # when fetching dhamma courses from dhamma.org, how many months to fetch starting from current month
    DAYS_TO_FETCH:int = 0 # when fetching dharma courses from dhamma.org, how many extra days to fetch after the last day of the last month (to catch late announcements)
    WAIT01_HOUR:int = 0
    WAIT01_MINS:int = 40
    WAIT02_HOUR:int = 1
    WAIT02_MINS:int = 20
    SHORT_DELAY:int = 4 # seconds: waiting time before uploading file to minio IN DEV MODE
    SENDING:str = "sending"
    RECEIVED:str = "received"
    CENTER_BUCKET:str = "centers-data" # bucket name for local center data 
    PI_BUCKET:str = "dhamma-gong-databases"  # bucket name for db exchange with Rasperry Pis
    DEV_USER:str = "spegoff@authentica.eu" # always forces short delay for all centers
    TEST_CENTER:str = "Testx" # always uses short delay, stops on confirmation error
    TEST_USER:str = "Usertest" # always uses short delay, stops on confirmation OK

Globals = GlobalsDefinition()

# ~/~ begin <<docs/gong-web-app-code/utilities.md#isdev-computer>>[init]

def show_load_context():
    hostname = socket.gethostname()
    container_name = os.getenv("CONTAINER_NAME", "unknown")
    if container_name == "unknown" and hostname in Globals.DEV_COMPUTERS:
        # 1. Get the absolute path to your project's root directory
        # (Assuming this script is running from your project root)
        BASE_DIR = Path(__file__).resolve().parent.parent
        SUB_DIR = BASE_DIR / ".devcontainer"
        # 2. Point directly to your custom file
        ENV_FILE_PATH = SUB_DIR / ".env.localhost"
        # 3. Load it explicitly
        load_dotenv(dotenv_path=ENV_FILE_PATH)
    print(f"hostname: {hostname}, container name: {container_name}, environ: {environ()}")

def environ():
    hostname = socket.gethostname()
    container_name = os.getenv("CONTAINER_NAME", "unknown")
    match container_name:
        case "vscodedev":
            enviro = "dev-container"
        case "staging":
            enviro = "staging-container"        
        case "unknown":
            if hostname in Globals.DEV_COMPUTERS:
                enviro = "dev-host"
            else:
            # on railway.com
                enviro = "prod-railway"
    return enviro

def get_db_path():
    if environ() != "prod-railway":
        root = ""
    else:   # Railway production permanent storage
        root = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH',"None") + "/"
    return root + "data/"

# ~/~ end
# ~/~ begin <<docs/gong-web-app-code/utilities.md#istest-db>>[init]
def isa_db_test(db):
    return 'Database <apsw.Connection object ""' in str(db)
# ~/~ end
# ~/~ begin <<docs/gong-web-app-code/utilities.md#send-email>>[init]

def send_email(subject, body, recipients):
    sender = Globals.EMAIL_SENDER
    if  "dev" in environ():
        print(f'From: {sender}\nTo: {recipients}\nSubject: {subject}\n\n{body}')
    else:
        resend_email(sender, subject, body, recipients)

def resend_email(sender, subject, body, recipients):
    # using resend
    resend.api_key = os.environ['RESEND_API_KEY']
    params: resend.Emails.SendParams = {
        "from": sender,
        "to": recipients,
        "subject": subject,
        "text": body,
    }
    email = resend.Emails.send(params)
    print(f'Message sent: {email} to {recipients} subject {subject}')
# ~/~ end
# ~/~ begin <<docs/gong-web-app-code/utilities.md#display-markdown>>[init]

def display_markdown(file_name:str, insert=None):
    file_path = os.path.join('md-text', f"{file_name}.md")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()
            if insert and "{{" in content and "}}" in content:
                new_content = content.split("{{", 1)[0] + insert + content.split("}}", 1)[1]
            else:
                new_content = content
            html_content = markdown2.markdown(new_content, extras={'breaks': {'on_newline': True, 'on_backslash': True}, 'tables':""})
        return NotStr(html_content)
    else:
        return f"!!! NO markdown file {file_name}.md IN md-text folder !!!"

def toggle_markdown(md_id: str, insert=None, showhelp=False):
    hidden = "hidden" if not showhelp else ""
    return Div(
        Button(
            "Show/Hide help text: ",B(f"{md_id.replace("-", " ").capitalize()}"),
            onclick=f"document.getElementById('{md_id}').classList.toggle('hidden')",
            style="background-color: olive; height: 24px; line-height: 22px; padding: 1px 5px; width: 400px;",
            cls="btn"
        ),
        Div(
            Blockquote(display_markdown(md_id, insert)),
            Hr(style="border: none; height: 3px; background-color: olive"),
            id=f"{md_id}",
            cls=f"markdown-block {hidden}"
        ),
        cls="toggle-markdown"
    )

# ~/~ end
# ~/~ begin <<docs/gong-web-app-code/utilities.md#plus-months-days>>[init]

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

def days_between_iso_dates(date_str1, date_str2):
    d1 = date.fromisoformat(date_str1)
    d2 = date.fromisoformat(date_str2)
    return (d2 - d1).days

def short_iso(date_time: datetime, timezon="UTC"):
    return date_time.astimezone(ZoneInfo(timezon)).strftime('%Y-%m-%dT%H:%M:%S%z')

def seconds_to_hours_minutes(total_seconds):
    hours = total_seconds // 3600
    remaining_minutes = (total_seconds % 3600) // 60
    return hours, remaining_minutes

# ~/~ end
# ~/~ begin <<docs/gong-web-app-code/utilities.md#pre-select-fasthtml>>[init]

def option_selected_one(value, current):
    return Option(
        value,
        value=value,
        **({"selected": True} if value == current else {})
    )

def option_selected_multi(value, selected_values):
    # Normalize both sides to strings for safe comparison
    sv = {str(v) for v in selected_values} if selected_values else set()
    return Option(
        value,
        value=value,
        **({"selected": True} if str(value) in sv else {})
    )

# ~/~ end
# ~/~ begin <<docs/gong-web-app-code/utilities.md#date-time-picker>>[init]

def TimePicker(name, value=None, id=None, label=None):
    id = id or f"{name}_picker"

    return Div(
        Label(label or name.capitalize(), _for=id),
        Input(
            id=id,
            name=name,
            value=value or "",
            placeholder="Select date & time",
            cls="dt-input"
        ),
        Script(f"""
            flatpickr("#{id}", {{
                enableTime: true,
                noCalendar: true,
                time_24hr: true,
                dateFormat: "H:i"
            }});
        """)
    )
# ~/~ end

# ~/~ end
