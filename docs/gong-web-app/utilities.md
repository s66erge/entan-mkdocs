# Utilities

- checking if the program runs on a development machine
- sending an email
- displaying the content of a markdown file
- route or function not implemented yet


```{.python file = libs/utils.py}
import socket
import calendar
import resend
import markdown2
import os
from datetime import datetime, date, timedelta
from fasthtml.common import *

class Globals:
    INITIAL_COUNTDOWN = 4000 # seconds

    @classmethod
    def get(cls, name, default=None):
        return getattr(cls, name, default)

<<dummy>>
<<isdev-computer>>
<<istest-db>>
<<send-email>>
<<display-markdown>>
<<plus-months-days>>
<<feedback-to-user>>
```
### Dummy start

```{.python #dummy}
def dummy():
    return "dummy"
```

### Check if the current computer is a development machine

This function checks if the program runs on one of a predefined list of development machines. This is useful to determine whether to use a local or remote base URL for building the registation link.

```{.python #isdev-computer}
def isa_dev_computer():
    DEV_COMPUTERS = ["serge-asrock","DESKTOP-UIPS8J2","serge-framework", "serge-bosgame", "Solaris" ]
    hostname = socket.gethostname()
    # print('hostname: '+hostname)
    return hostname in DEV_COMPUTERS
```

### Check if current db is a teporary db in memory

```{.python #istest-db}
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

```{.python #send-email}

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

```{.python #display-markdown}

def display_markdown(file_name:str):
    file_path = os.path.join('md-text', f"{file_name}.md")
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            html_content = markdown2.markdown(f.read())
        return NotStr(html_content)
    else:
        return f"!!! NO markdown file {file_name}.md IN md-text folder !!!"
```

### Add months and days to an ISO date

Return an ISO date string num_months and num_days after date_str (YYYY-MM-DD).
Uses divmod to compute year/month rollover and preserves end-of-month.

```{.python #plus-months-days}

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
```

### Success/error message

```{.python #feedback-to-user}

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
        'planner_deleted': 'Planner association deleted successfully!'
    }
    error_messages = {
        'missing_email':'Email is required.',
        'not_registered':f'Email "{params.get("email", "")}" is not registered, try again or send a message to xxx@xxx.xx to get registered',
        'invalid_or_expired_code': 'The code is invalid ot expired. Check if if it is correct. Or refresh the page to ask for another code.',
        'missing_fields': 'Please fill in all required fields.',
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
        'last_planner_for_center': f'Cannot delete planner. This is the last planner for center: "{params.get("center", "")}". Each center must have at least one planner.'
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
            Div(P(mess_dict['mess']), style="color: #daecdaff; background: #187449ff; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #198754; font-weight: 500;"),
            Small("To clear this message and/or update the tables, reload the page")
        )
    elif mess_dict["res"] == 'error':
        message_div = Div(
            Div(P(mess_dict['mess']), style="color: #f8d7da; background: #842029; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #dc3545; font-weight: 500;"),
            Small("To clear this message, reload the page")
        )
    return message_div
```
