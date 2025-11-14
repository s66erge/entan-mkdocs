# ~/~ begin <<docs/gong-web-app/utilities.md#libs/utils.py>>[init]
import socket
import resend
import markdown2
from fasthtml.common import *

# ~/~ begin <<docs/gong-web-app/utilities.md#isa-dev-computer>>[init]

DEV_COMPUTERS = ["serge-asrock","DESKTOP-UIPS8J2","serge-virtual-linuxmint","serge-framework"]
def isa_dev_computer():
    hostname = socket.gethostname()
    return hostname in DEV_COMPUTERS
# ~/~ end
# ~/~ begin <<docs/gong-web-app/utilities.md#send-email>>[init]

def send_email(subject, body, recipients):
    # old code via smtp
    """
    sender = os.environ.get('GOOGLE_SMTP_USER') 
    password = os.environ.get('GOOGLE_SMTP_PASS')
    # Create MIMEText email object with the email body
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    # Connect securely to Gmail SMTP server and login
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
    """
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
# ~/~ end
