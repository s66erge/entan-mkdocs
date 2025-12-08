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
from datetime import datetime, date, timedelta
from fasthtml.common import *

<<dummy>>
<<isdev-computer>>
<<istest-db>>
<<send-email>>
<<display-markdown>>
<<plus-months-days>>
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
    DEV_COMPUTERS = ["serge-asrock","DESKTOP-UIPS8J2","serge-virtual-linuxmint","serge-framework" ]
    hostname = socket.gethostname()
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
    print(f'Message sent: {email}')
```

### Displaying the content of a markdown file

This function reads a markdown file name, without the extension '.md', then finds the file in the 'md-text' directory and converts it to HTML using the `markdown2` library, which is then returned as a NotStr object for rendering in the app.

```{.python #display-markdown}

def display_markdown(file_name:str):
    with open(f'md-text/{file_name}.md', "r") as f:
        html_content = markdown2.markdown(f.read())
    return NotStr(html_content)
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
