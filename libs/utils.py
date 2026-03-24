# ~/~ begin <<docs/gong-web-app/utilities.md#libs/utils.py>>[init]

import socket
import tempfile
import calendar
import json
from enum import Enum
from zoneinfo import ZoneInfo
from fasthtml.common import *
import resend 
import markdown2
import os
from datetime import datetime, date, timedelta

temp_paths = {}

class Globals:
    INITIAL_COUNTDOWN = 4000 # seconds before auto-abandoning an edit session, set in planning_page and used in JS_CLIENT_TIMER
    SUBDIR_TEMP = "temp" # subdir of get_db_path() for temp files
    MONTHS_TO_FETCH = 12 # when fetching dhamma courses from dhamma.org, how many months to fetch starting from current month
    DAYS_TO_FETCH = 0 # when fetching dharma courses from dhamma.org, how many extra days to fetch after the last day of the last month (to catch late announcements)
    SHORT_DELAY = 3 # seconds: waiting time before uploading file to Pi IN DEV MODE
    PI_FOLDER_TEST = "/home/pi/test"  # PI folder used for ssh get/put tests
    PI_FILE_TEST = "test22.json"  # file used for ssh get/put tests with PI
    DEV_USER = "spegoff@authentica.eu" # IN PROD: can force state to free AND TEMPORALY SAVE CHANGES
    TEST_CENTER = "Testx" # used for testing in DEV mode
    @classmethod
    def get(cls, name, default=None):
        return getattr(cls, name, default)

# ~/~ begin <<docs/gong-web-app/utilities.md#isdev-computer>>[init]
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
    return isa_dev_computer() or session["auth"] == Globals.DEV_USER

# ~/~ end
# ~/~ begin <<docs/gong-web-app/utilities.md#istest-db>>[init]
def isa_db_test(db):
    return 'Database <apsw.Connection object ""' in str(db)
# ~/~ end
# ~/~ begin <<docs/gong-web-app/utilities.md#send-email>>[init]

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
# ~/~ end
# ~/~ begin <<docs/gong-web-app/utilities.md#display-markdown>>[init]

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
# ~/~ end
# ~/~ begin <<docs/gong-web-app/utilities.md#temp-files>>[init]

def create_temp_path(center):
    temp_dir = get_db_path() + Globals.SUBDIR_TEMP 
    with tempfile.NamedTemporaryFile(mode='w', delete=False, dir=temp_dir) as tmp_file:
        temp_paths[center] = tmp_file.name

def delete_temp_path(center):
    if center in temp_paths and os.path.exists(temp_paths[center]):
        os.unlink(temp_paths[center])
    temp_paths[center] = ""

def wipe_all_temps():
    temp_dir =  get_db_path() + Globals.SUBDIR_TEMP
    for filename in os.listdir(temp_dir):
        file_path = os.path.join(temp_dir, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

def get_all_center_data(center):
    temp_path = temp_paths[center]
    with open(temp_path, 'r') as f:
        content = f.read()
        return json.loads(content) if content else {}

def save_all_center_data(center, data):
    temp_path = temp_paths[center]
    with open(temp_path, "w") as f:
        f.write(json.dumps(data, default=str))

def get_center_data(center, key):
    center_data = get_all_center_data(center)
    return center_data[key]

def save_center_data(center, key, data):
    center_data = get_all_center_data(center)
    center_data[key] = data
    save_all_center_data(center, center_data)

# ~/~ end
# ~/~ begin <<docs/gong-web-app/utilities.md#plus-months-days>>[init]

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

# ~/~ end
# ~/~ begin <<docs/gong-web-app/utilities.md#feedback-to-user>>[init]

def feed_text(params):
    # query_params = dict(request.query_params)
    # Handle success and error messages
    success_messages = {
        'login_code_sent': "A code to sign in has been sent to your email. Please check your inbox and enter the code here below. The code will expire in 15 minutes.",
        'user_added': 'User added successfully!',
        'center_added': 'Center added successfully!',
        'planner_added': 'Planner association adSded successfully!',
        'user_deleted': 'User deleted successfully!',
        'center_deleted': 'Center and associated database deleted successfully!',
        'planner_deleted': 'Planner association deleted successfully!',
        'new_course': 'New line added. Please review the plan and submit changes to update the center gong.',
        'line_deleted': 'Line deleted. Please review the plan and submit changes to update the center gong.',
        'show_plan': 'Here is the plan you already worked on.',
        'config_uploaded': "New configuration loaded in database",
        'config_downloaded': "Configuration in database downloaded"
    }
    error_messages = {
        'missing_email':'Email is required.',
        'not_registered':f'Email "{params.get("email", "")}" is not registered, try again or send a message to xxx@xxx.xx to get registered',
        'invalid_or_expired_code': 'The code is invalid ot expired. Check if if it is correct. Or refresh the page to ask for another code.',
        'missing_fields': 'Please fill in all required fields.',
        'plan_not_ok': 'Correct the planning errors before saving this plan',
        'user_exists': 'User with this email already exists.',
        'center_exists': 'Center with this name already exists.',
        'planner_exists': 'This planner association already exists.',
        'user_not_found': 'User not found.',
        'center_not_found': 'Center not found.',
        'invalid_role': 'Invalid role selected.',
        'db_error': f'Database error occurred: {params.get("etext", "")}. Please contact the program support.',
        'db_file_exists': 'Database file with this name already exists.',
        'template_not_found': 'Template database (mahi.db) not found.',
        'user_has_planners': f'Cannot delete user. User is still associated with centers: {params.get("centers", "")}. Please remove all planner associations first.',
        'center_has_planners': f'Cannot delete center. Center is still associated with users: {params.get("users", "")}. Please remove all planner associations first.',
        'last_planner_for_center': f'Cannot delete planner. This is the last planner for center: "{params.get("center", "")}". Each center must have at least one planner.',
        'bad_config_filename': 'The filename does not match the center name and/or is nor a .xslx excel file'
    }
    message = ""
    result = ""
    if 'success' in params:
        message = success_messages.get(params['success'], 'Operation completed successfully!')
        result = "success"
    elif 'error' in params:
        message = error_messages.get(params['error'], 'An error occurred.')
        result = "error"
    return {"mess": message, "res": result}

def feedback_to_user(params):
    # query_params = dict(request.query_params)
    # Handle success and error messages
    mess_dict = feed_text(params)
    message_div = Div(P(""))
    if mess_dict["res"] == 'success':
        message_div = Div(
            Div(P(mess_dict['mess']), style="color: #daecdaff; background: #187449ff; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #198754; font-weight: 500;")
        )
    elif mess_dict["res"] == 'error':
        message_div = Div(
            Div(P(mess_dict['mess']), style="color: #f8d7da; background: #842029; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #dc3545; font-weight: 500;")
        )
    return message_div
# ~/~ end
# ~/~ end
