# Utilities

- sending an email
- displaying the content of a markdown file

``` {.python #utilities-md}

<<send-email>>
<<display-markdown>>

```

### Send email via Google smtp

We will need to create an App Password in your Google Account settings as we have 2-Step Verification enabled.

Example for using: *send_email(subject, body, recipients, password)*

- subject = "Hello from Python"
- body = "This is a test email sent from Python using Gmail SMTP."
- recipients = ["recipient1@gmail.com"]  : list of recipients
- password = "your_app_password" : in production in "GOOGLE_SMTP_PASS" environment variable 

``` {.python #send-email}

def send_email(subject, body, recipients, password):
    # Create MIMEText email object with the email body
    sender = "spegoff@authentica.eu" 

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

``` {.python #display-markdown}

def display_markdown(file_path):
    with open(file_path, "r") as f:
        html_content = markdown2.markdown(f.read())
    return NotStr(html_content)

```

