# ~/~ begin <<docs/gong-web-app/utilities.md#libs/utils.py>>[init]
import socket
import calendar
import resend
import markdown2
from datetime import datetime, date, timedelta
from fasthtml.common import *

# ~/~ begin <<docs/gong-web-app/utilities.md#dummy>>[init]
def dummy():
    return "dummy"
# ~/~ end
# ~/~ begin <<docs/gong-web-app/utilities.md#isdev-computer>>[init]
def isa_dev_computer():
    DEV_COMPUTERS = ["serge-asrock","DESKTOP-UIPS8J2","serge-virtual-linuxmint","serge-framework" ]
    hostname = socket.gethostname()
    return hostname in DEV_COMPUTERS
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
    print(f'Message sent: {email}')
# ~/~ end
# ~/~ begin <<docs/gong-web-app/utilities.md#display-markdown>>[init]

def display_markdown(file_name:str):
    with open(f'md-text/{file_name}.md', "r") as f:
        html_content = markdown2.markdown(f.read())
    return NotStr(html_content)
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
# ~/~ end
# ~/~ end
