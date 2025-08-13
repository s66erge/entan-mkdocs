# Utilities

- checking if the program runs on a development machine
- sending an email
- displaying the content of a markdown file

``` {.python #utilities-md}

<<isa-dev-computer>>
<<send-email>>
<<display-markdown>>
```

### Check if the current computer is a development machine

This function checks if the program runs on one of a predefined list of development machines. This is useful to determine whether to use a local or remote base URL for building the registation link.

``` {.python #isa-dev-computer}

DEV_COMPUTERS = ["ASROCK-MY-OFFICE","DESKTOP-UIPS8J2","serge-virtual-machine"]
def isa_dev_computer():
    hostname = socket.gethostname()
    return hostname in DEV_COMPUTERS
```

### Send email via Google smtp

We will need to create an App Password in your Google Account settings as we have 2-Step Verification enabled.

Example for using: *send_email(subject, body, recipients)*

- subject = "Hello from Python"
- body = "This is a test email sent from Python using Gmail SMTP."
- recipients = ["recipient1@gmail.com"]  : list of recipients 

``` {.python #send-email}

def send_email(subject, body, recipients):
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
    print("Message sent!")
```

### Displaying the content of a markdown file

This function reads a markdown file name, without the extension '.md', then finds the file in the 'md-text' directory and converts it to HTML using the `markdown2` library, which is then returned as a NotStr object for rendering in the app.

``` {.python #display-markdown}

def display_markdown(file_name:str):
    with open(f'md-text/{file_name}.md', "r") as f:
        html_content = markdown2.markdown(f.read())
    return NotStr(html_content)
```

